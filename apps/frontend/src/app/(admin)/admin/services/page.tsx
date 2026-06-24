"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type Service } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, FormField, Textarea, Modal, Alert, PageSpinner, Badge } from "@/components/ui/index";
import { Plus, Pencil, Trash2 } from "lucide-react";

const BLANK: Partial<Service> = {
  name: { en: "", es: "" },
  description: { en: "", es: "" },
  durationMinutes: 50,
  active: true,
};

export default function AdminServicesPage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<Partial<Service> | null>(null);
  const [isNew, setIsNew] = useState(false);
  const [formError, setFormError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin-services"],
    queryFn: () => api.admin.services(),
  });

  const saveMutation = useMutation({
    mutationFn: (svc: Partial<Service>) =>
      svc.serviceId
        ? api.admin.updateService(svc.serviceId, svc)
        : api.admin.createService(svc),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-services"] });
      setEditing(null);
    },
    onError: (e: Error) => setFormError(e.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.admin.deleteService(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-services"] }),
  });

  const openNew  = () => { setEditing({ ...BLANK }); setIsNew(true);  setFormError(""); };
  const openEdit = (svc: Service) => { setEditing({ ...svc }); setIsNew(false); setFormError(""); };

  const handleSave = () => {
    if (!editing?.name?.en) { setFormError("English name is required"); return; }
    saveMutation.mutate(editing);
  };

  const services = data?.services ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="heading-section">Services</h1>
          <p className="text-[var(--color-muted)] mt-1">Manage the services clients can book</p>
        </div>
        <Button onClick={openNew}><Plus className="w-4 h-4" />Add Service</Button>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {services.map((svc) => (
            <div key={svc.serviceId} className="card flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium text-[var(--color-text)]">{svc.name.en}</h3>
                    {!svc.active && <Badge status="cancelled" />}
                  </div>
                  {svc.name.es && (
                    <p className="text-xs text-[var(--color-muted)]">{svc.name.es}</p>
                  )}
                </div>
                <span className="text-sm text-[var(--color-muted)] flex-shrink-0">
                  {svc.durationMinutes} min
                </span>
              </div>
              <p className="text-sm text-[var(--color-muted)] leading-relaxed flex-1">
                {svc.description.en}
              </p>
              <div className="flex gap-2 pt-2 border-t border-[var(--color-border)]">
                <Button size="sm" variant="outline" onClick={() => openEdit(svc)}>
                  <Pencil className="w-3.5 h-3.5" />Edit
                </Button>
                <Button
                  size="sm" variant="ghost"
                  onClick={() => svc.active && deleteMutation.mutate(svc.serviceId)}
                  className="text-red-500 hover:text-red-600 hover:bg-red-50"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  {svc.active ? "Deactivate" : "Inactive"}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit/Create modal */}
      <Modal
        open={!!editing}
        onClose={() => setEditing(null)}
        title={isNew ? "Add Service" : "Edit Service"}
      >
        {editing && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <FormField label="Name (English)" required>
                <Input
                  value={editing.name?.en || ""}
                  onChange={(e) => setEditing({ ...editing, name: { ...editing.name, en: e.target.value } })}
                  placeholder="Individual Therapy"
                />
              </FormField>
              <FormField label="Name (Español)">
                <Input
                  value={editing.name?.es || ""}
                  onChange={(e) => setEditing({ ...editing, name: { ...editing.name, es: e.target.value } })}
                  placeholder="Terapia Individual"
                />
              </FormField>
            </div>
            <FormField label="Description (English)">
              <Textarea
                rows={2}
                value={editing.description?.en || ""}
                onChange={(e) => setEditing({ ...editing, description: { ...editing.description, en: e.target.value } })}
              />
            </FormField>
            <FormField label="Description (Español)">
              <Textarea
                rows={2}
                value={editing.description?.es || ""}
                onChange={(e) => setEditing({ ...editing, description: { ...editing.description, es: e.target.value } })}
              />
            </FormField>
            <FormField label="Duration (minutes)">
              <Input
                type="number"
                min={15} max={240} step={5}
                value={editing.durationMinutes || 50}
                onChange={(e) => setEditing({ ...editing, durationMinutes: parseInt(e.target.value) })}
              />
            </FormField>

            {formError && <Alert type="error">{formError}</Alert>}

            <div className="flex gap-3 pt-2">
              <Button variant="ghost" fullWidth onClick={() => setEditing(null)}>Cancel</Button>
              <Button fullWidth loading={saveMutation.isPending} onClick={handleSave}>
                {isNew ? "Create Service" : "Save Changes"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
