"use client";

import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { api, type User } from "@/lib/api";
import { Badge, PageSpinner, Alert } from "@/components/ui/index";
import { Users } from "lucide-react";

export default function AdminUsersPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.admin.users(),
  });

  const users = data?.users ?? [];

  return (
    <div>
      <div className="mb-8">
        <h1 className="heading-section">Users</h1>
        <p className="text-[var(--color-muted)] mt-1">{data?.count ?? 0} registered accounts</p>
      </div>

      {isLoading ? (
        <PageSpinner />
      ) : error ? (
        <Alert type="error">Could not load users.</Alert>
      ) : users.length === 0 ? (
        <div className="card text-center py-12">
          <Users className="w-12 h-12 text-[var(--color-muted)] mx-auto mb-3" />
          <p className="text-[var(--color-muted)]">No users registered yet.</p>
        </div>
      ) : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                  {["Name", "Email", "Phone", "Verified", "Role", "Joined"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-medium text-[var(--color-muted)]">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {users.map((user) => (
                  <UserRow key={user.userId} user={user} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function UserRow({ user }: { user: User }) {
  return (
    <tr className="hover:bg-[var(--color-surface)] transition-colors">
      <td className="px-4 py-3 font-medium text-[var(--color-text)]">
        {user.firstName} {user.lastName}
      </td>
      <td className="px-4 py-3 text-[var(--color-muted)]">{user.email}</td>
      <td className="px-4 py-3 text-[var(--color-muted)]">{user.phone || "—"}</td>
      <td className="px-4 py-3">
        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full
          ${user.verified ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
          {user.verified ? "✓ Verified" : "Pending"}
        </span>
      </td>
      <td className="px-4 py-3">
        <Badge status={user.role === "admin" ? "accepted" : "default"} />
      </td>
      <td className="px-4 py-3 text-[var(--color-muted)]">
        {user.createdAt ? format(new Date(user.createdAt), "MMM d, yyyy") : "—"}
      </td>
    </tr>
  );
}
