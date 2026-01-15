# NetSuite API Best Practices

This document provides best practices for optimizing API usage and staying within governance limits.

## 1. Authentication Best Practices

### Token-Based Authentication (Recommended)

```
Benefits:
✓ No session management overhead
✓ Better for concurrent requests
✓ Stateless - easier to scale
✓ More secure than credentials
```

### Implementation Tips

1. **Generate tokens per environment**
   - Separate tokens for dev/test/prod
   - Never share tokens across environments

2. **Token rotation**
   - Rotate tokens periodically
   - Implement token refresh logic

3. **Secure storage**
   - Store in encrypted vault
   - Never commit to source control

---

## 2. Search Optimization

### Use Indexed Fields

| Always Filter On | Reason |
|------------------|--------|
| internalId | Primary key, always indexed |
| lastModifiedDate | Indexed for incremental |
| type | Reduces scan scope |
| subsidiary | Partitions data |

### Avoid These Patterns

| Anti-Pattern | Issue | Alternative |
|--------------|-------|-------------|
| `SELECT *` | Returns all fields | Use SearchRow |
| No date filters | Full table scan | Add date range |
| Complex joins | Slow queries | Separate searches |
| Very wide date ranges | Too many results | Narrower windows |

### Efficient Search Example

```java
// Good: Specific columns, date filter, type filter
TransactionSearchAdvanced search = new TransactionSearchAdvanced();
TransactionSearch criteria = new TransactionSearch();
TransactionSearchBasic basic = new TransactionSearchBasic();

// Date filter (incremental)
SearchDateField lastModified = new SearchDateField();
lastModified.setOperator(SearchDateFieldOperator.ON_OR_AFTER);
lastModified.setSearchValue(lastSyncDate);
basic.setLastModifiedDate(lastModified);

// Type filter
SearchEnumMultiSelectField typeFilter = new SearchEnumMultiSelectField();
typeFilter.setOperator(SearchEnumMultiSelectFieldOperator.ANY_OF);
typeFilter.setSearchValue(new String[]{"_invoice", "_salesOrder"});
basic.setType(typeFilter);

criteria.setBasic(basic);
search.setCriteria(criteria);

// Return only needed columns
TransactionSearchRow columns = new TransactionSearchRow();
TransactionSearchRowBasic rowBasic = new TransactionSearchRowBasic();
rowBasic.setInternalId(new SearchColumnSelectField());
rowBasic.setTranId(new SearchColumnStringField());
rowBasic.setTranDate(new SearchColumnDateField());
columns.setBasic(rowBasic);
search.setColumns(columns);
```

---

## 3. Pagination Best Practices

### Always Use searchMoreWithId

```
Benefits:
✓ Server maintains search context
✓ Consistent results across pages
✓ More efficient than re-searching
```

### Page Through All Results

```python
# Python pseudocode
def fetch_all_records(search_criteria):
    all_records = []
    
    # Initial search
    response = client.search(search_criteria)
    all_records.extend(response.records)
    
    search_id = response.searchId
    total_pages = response.totalPages
    
    # Page through results
    for page in range(2, total_pages + 1):
        page_response = client.searchMoreWithId(search_id, page)
        all_records.extend(page_response.records)
        
        # Respect rate limits
        time.sleep(0.1)
    
    return all_records
```

---

## 4. Concurrent Request Management

### Client-Side Queue

```python
from concurrent.futures import ThreadPoolExecutor
import threading

class RateLimitedClient:
    def __init__(self, max_concurrent=5):
        self.semaphore = threading.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    def execute(self, func, *args):
        with self.semaphore:
            return func(*args)
```

### Concurrency Guidelines

| Account Size | Recommended Threads |
|--------------|---------------------|
| Small (Tier 1-2) | 2-3 |
| Medium (Tier 3) | 5-8 |
| Large (Tier 4-5) | 10-20 |

---

## 5. Error Handling

### Implement Retry Logic

```python
import time
import random

def retry_with_exponential_backoff(func, max_retries=5):
    """
    Retry function with exponential backoff and jitter.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except (ConcurrencyError, RateLimitError) as e:
            if attempt == max_retries - 1:
                raise
            
            # Exponential backoff with jitter
            wait_time = min(32, (2 ** attempt)) + random.uniform(0, 1)
            print(f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s")
            time.sleep(wait_time)
        except (AuthenticationError, PermissionError):
            # Don't retry auth/permission errors
            raise
```

### Error Classification

| Error Type | Retry? | Action |
|------------|--------|--------|
| Concurrency | Yes | Wait, backoff |
| Rate limit | Yes | Wait, backoff |
| Timeout | Yes | Simplify query |
| Authentication | No | Check credentials |
| Permission | No | Check role |
| Validation | No | Fix request |

---

## 6. Caching Strategies

### What to Cache

| Data Type | Cache Duration | Storage |
|-----------|----------------|---------|
| Subsidiary list | 24 hours | Memory/Redis |
| Department list | 24 hours | Memory/Redis |
| Location list | 24 hours | Memory/Redis |
| Tax codes | 24 hours | Memory/Redis |
| Currency rates | 1 hour | Memory/Redis |

### Cache-Aside Pattern

```python
def get_subsidiaries(client, cache):
    cache_key = "netsuite:subsidiaries"
    
    # Check cache first
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from API
    subsidiaries = client.search_subsidiaries()
    
    # Store in cache
    cache.set(cache_key, subsidiaries, ttl=86400)
    
    return subsidiaries
```

---

## 7. Data Volume Strategies

### Large Dataset Handling

| Strategy | Use Case |
|----------|----------|
| Date windowing | Split by time periods |
| Type filtering | Process one type at a time |
| Subsidiary filtering | Process one subsidiary at a time |
| Parallel processing | Multiple concurrent streams |

### Date Window Example

```python
def sync_by_date_windows(start_date, end_date, window_days=7):
    """
    Split large date ranges into smaller windows.
    """
    current = start_date
    while current < end_date:
        window_end = min(current + timedelta(days=window_days), end_date)
        
        # Sync this window
        sync_records(current, window_end)
        
        current = window_end
```

---

## 8. Monitoring and Alerting

### Key Metrics

| Metric | Warning | Critical |
|--------|---------|----------|
| Error rate | > 2% | > 5% |
| Avg latency | > 5s | > 15s |
| Concurrency usage | > 70% | > 90% |
| Daily API calls | > 80% quota | > 95% quota |

### Logging Best Practices

```python
# Log essential information
logger.info(f"Search started: type={record_type}, filter={date_filter}")
logger.info(f"Search complete: records={count}, pages={pages}, duration={duration}s")
logger.warning(f"Retry required: attempt={attempt}, error={error_code}")
logger.error(f"Search failed: error={error}, request_id={request_id}")
```

---

## 9. Security Best Practices

### Token Security

- Store tokens in encrypted secrets management
- Use environment variables, not config files
- Rotate tokens every 90 days
- Use separate tokens per environment

### Network Security

- Use TLS 1.2 or higher
- Validate SSL certificates
- Consider IP allowlisting
- Monitor for unusual activity

### Audit Trail

- Log all API operations
- Include user/integration context
- Retain logs for compliance period
- Review logs regularly

---

## 10. Performance Checklist

### Before Go-Live

- [ ] Implemented token-based auth
- [ ] Optimized searches with filters
- [ ] Using SearchRow for column selection
- [ ] Retry logic implemented
- [ ] Caching for reference data
- [ ] Monitoring in place
- [ ] Alerts configured
- [ ] Load tested with production data volume

### Ongoing

- [ ] Weekly performance review
- [ ] Monthly API usage analysis
- [ ] Quarterly token rotation
- [ ] Regular error log review
