# NetSuite API Governance and Limits

This document details the governance rules, rate limits, and quotas for NetSuite Web Services APIs.

## 1. Governance Overview

NetSuite uses a governance framework to ensure fair resource allocation across all users. Key concepts:

- **Concurrency Limits**: Maximum simultaneous API requests
- **Unit Limits**: Governance units consumed per operation
- **Request Limits**: Maximum requests per time period

---

## 2. Concurrency Limits

### 2.1 By Service Tier

| Service Tier | Concurrent Requests | Notes |
|--------------|---------------------|-------|
| Tier 1 | 5 | Standard accounts |
| Tier 2 | 10 | Mid-size accounts |
| Tier 3 | 15 | Enterprise accounts |
| Tier 4 | 25 | Large enterprise |
| Tier 5 | 50+ | SuiteCloud Plus |

### 2.2 SuiteCloud Plus Licenses

Additional concurrent request capacity can be purchased:

| Licenses | Additional Concurrency |
|----------|----------------------|
| 1 | +10 concurrent |
| 2 | +20 concurrent |
| 5 | +50 concurrent |

### 2.3 Checking Concurrency Usage

Monitor via:
- **Setup > Integration > Web Services Usage Log**
- Response headers: `X-N-ConcurrencyInfo`

---

## 3. Governance Units

### 3.1 Operation Costs

| Operation | Governance Units |
|-----------|------------------|
| search | 10 per call |
| searchMore | 10 per call |
| searchMoreWithId | 10 per call |
| get | 5 per record |
| getList | 5 per record |
| add | 10 per record |
| update | 10 per record |
| delete | 10 per record |
| upsert | 10 per record |
| getDeleted | 10 per call |

### 3.2 Daily Unit Limits

| Account Type | Daily Units |
|--------------|-------------|
| Standard | Varies by tier |
| Enterprise | Higher limits |
| SuiteCloud Plus | Unlimited* |

*Subject to concurrency limits

---

## 4. Request Size Limits

### 4.1 Search Limits

| Parameter | Limit |
|-----------|-------|
| Page size | 1,000 records max |
| Total results | 1,000,000 per search |
| Search timeout | 180 seconds |
| Search columns | 100 max |

### 4.2 Record Limits

| Parameter | Limit |
|-----------|-------|
| GetList batch | 1,000 records |
| Sublist lines | 4,000 per record |
| Custom fields | 500 per record type |

### 4.3 Request Body Limits

| Limit Type | Value |
|------------|-------|
| SOAP request size | 50 MB |
| REST request size | 10 MB |
| Response timeout | 360 seconds |

---

## 5. Rate Limiting

### 5.1 Request Rate

| Context | Limit |
|---------|-------|
| Per integration | Based on concurrency |
| Per user | Shared across integrations |
| Per account | Sum of all users |

### 5.2 Throttling Behavior

When limits are exceeded:
1. Request queued (if within buffer)
2. `EXCEEDED_CONCURRENT_REQUEST_LIMIT` error
3. Exponential backoff recommended

### 5.3 Retry Strategy

```python
# Recommended retry approach
def retry_with_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except ConcurrencyError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
    raise MaxRetriesExceeded()
```

---

## 6. Error Codes

### 6.1 Governance Errors

| Error Code | Description | Action |
|------------|-------------|--------|
| `EXCEEDED_CONCURRENT_REQUEST_LIMIT` | Too many concurrent requests | Wait and retry |
| `EXCEEDED_REQUEST_LIMIT` | Rate limit exceeded | Backoff and retry |
| `EXCEEDED_REQUEST_SIZE` | Request too large | Reduce batch size |
| `WS_CONCUR_SESSION_DISALLWD` | Session concurrency issue | Use stateless requests |
| `WS_REQUEST_BLOCKED` | Request blocked | Check IP restrictions |

### 6.2 Timeout Errors

| Error Code | Description | Action |
|------------|-------------|--------|
| `SSS_TIME_LIMIT_EXCEEDED` | Script timeout | Simplify query |
| `SEARCH_TIMED_OUT` | Search timeout | Add filters, reduce scope |

---

## 7. Best Practices

### 7.1 Optimize API Usage

| Practice | Benefit |
|----------|---------|
| Use incremental sync | Reduce record count |
| Select specific columns | Reduce response size |
| Batch operations | Reduce request count |
| Cache reference data | Reduce redundant calls |

### 7.2 Efficient Searches

| Technique | Description |
|-----------|-------------|
| Index fields in filters | Use indexed fields like internalId |
| Limit returned columns | Use SearchRow |
| Use date ranges | Narrow result sets |
| Avoid cross joins | Simplify search criteria |

### 7.3 Connection Management

| Practice | Recommendation |
|----------|----------------|
| Connection pooling | Reuse HTTP connections |
| Session management | Prefer token-based auth |
| Parallel requests | Stay within concurrency |
| Request queuing | Implement client-side queue |

---

## 8. Monitoring and Alerts

### 8.1 Usage Monitoring

```
Setup > Integration > Web Services Usage Log
- Filter by date, user, operation
- View request counts, errors
- Export for analysis
```

### 8.2 Key Metrics to Track

| Metric | Threshold | Action |
|--------|-----------|--------|
| Concurrent requests | > 80% of limit | Scale back or upgrade |
| Error rate | > 5% | Investigate issues |
| Avg response time | > 10 seconds | Optimize queries |
| Daily unit usage | > 90% | Review efficiency |

---

## 9. Integration Checklist

### Pre-Production

- [ ] Determine account service tier
- [ ] Calculate expected API volume
- [ ] Implement retry logic
- [ ] Test with production-like data
- [ ] Set up monitoring

### Production

- [ ] Monitor concurrency utilization
- [ ] Track error rates
- [ ] Review performance weekly
- [ ] Scale as needed

---

## 10. Connector Recommendations

### 10.1 Default Settings

| Setting | Recommended Value |
|---------|-------------------|
| Concurrent threads | 3-5 (conservative) |
| Page size | 1000 |
| Retry attempts | 5 |
| Retry backoff | Exponential (1-32 sec) |
| Request timeout | 180 seconds |

### 10.2 High Volume Accounts

| Setting | Recommended Value |
|---------|-------------------|
| Concurrent threads | Up to concurrency limit |
| Batch size | Maximum (1000) |
| Sync frequency | Based on data volume |
