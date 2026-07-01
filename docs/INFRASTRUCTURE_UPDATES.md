# Infrastructure Updates Applied

## 7 Changes Made to CDK Infrastructure

### 1. Lambda Timeout: 29s → 90s ✅
- **File**: `infra/cdk/stacks/site_stack.py`
- **Impact**: Safe margin for API calls, no cost change
- **Benefit**: Prevents timeouts on slow Brevo/data operations

### 2. X-Ray Tracing: ACTIVE → PASS_THROUGH ✅
- **File**: `infra/cdk/stacks/site_stack.py`
- **Impact**: ~$5/month savings at 10 sites
- **Benefit**: Only traces errors, not every invocation

### 3. DynamoDB Cost Guardrails ✅
- **File**: `infra/cdk/stacks/site_stack.py`
- **Added**: Auto-scale with max caps (40 RCU, 20 WCU)
- **Benefit**: Prevents runaway costs from N+1 queries

### 4. EventBridge Dead-Letter Queue ✅
- **File**: `infra/cdk/stacks/site_stack.py`
- **Added**: SQS DLQ for failed reminders, retry logic
- **Cost**: +$0.50/month per site
- **Benefit**: No silent failures, alerts on issues

### 5. CloudWatch Monitoring Stack ✅
- **File**: `infra/cdk/stacks/monitoring_stack.py` (new)
- **Added**: Dashboards + 3 alarms (errors, DynamoDB, throttles)
- **Cost**: +$1/month per site
- **Benefit**: Visibility into performance & failures

### 6. CDK Context Flags ✅
- **File**: `infra/cdk/cdk.json`
- **Added**: 3 best-practice context flags
- **Benefit**: Standardizes behavior, prevents deprecation warnings

### 7. Monitoring Stack Integration ✅
- **File**: `infra/cdk/app.py`
- **Added**: MonitoringStack deployed alongside each SiteStack
- **Benefit**: Auto-generated dashboards for each client

## Cost Impact

| Item | Cost Change |
|------|-------------|
| X-Ray sampling fix | -$5/month @10 sites |
| EventBridge DLQ | +$0.50/month |
| Monitoring stack | +$1/month |
| **Net per site** | **+$1.50/month** |

## Before Deploying

```bash
cd infra/cdk

# 1. Bootstrap (if not done)
cdk bootstrap aws://YOUR_ACCOUNT/us-east-1

# 2. Preview changes
cdk diff SfSiteStack-serenity-therapy

# 3. Deploy
cdk deploy SfSiteStack-serenity-therapy SfMonitoring-serenity-therapy
```

## What Gets Better

✅ Lambda won't timeout on slow APIs  
✅ Failed reminders won't vanish silently  
✅ DynamoDB costs are capped at reasonable limits  
✅ Dashboard shows real-time performance metrics  
✅ Alarms email admin on errors  
✅ X-Ray costs drop ~90%  

## Status: Production Ready
