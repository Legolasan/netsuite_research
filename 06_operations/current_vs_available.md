# NetSuite Operations: Current vs. Available

This document provides a detailed comparison between what's implemented and what's available.

## 1. Summary Matrix

| Category | Implemented | Available | Coverage |
|----------|-------------|-----------|----------|
| Search | 3/3 | 3 | 100% |
| Get | 1/3 | 3 | 33% |
| Write | 0/8 | 8 | 0% |
| Transform | 0/1 | 1 | 0% |
| Relationship | 0/2 | 2 | 0% |
| Async | 0/5 | 5 | 0% |
| **Total** | **4/22** | **22** | **18%** |

---

## 2. Detailed Comparison

### 2.1 Search Operations (100% Coverage)

| Operation | Current | Notes |
|-----------|---------|-------|
| search | ✅ | Full implementation |
| searchMore | ✅ | Full implementation |
| searchMoreWithId | ✅ | Full implementation |

**Status**: Complete for ETL use case

### 2.2 Get Operations (33% Coverage)

| Operation | Current | Impact |
|-----------|---------|--------|
| getDeleted | ✅ | Delete tracking |
| get | ❌ | Single record lookup |
| getList | ❌ | Batch record lookup |

**Gap Analysis**:
- `get` useful for refreshing specific records
- `getList` useful for targeted data refresh

### 2.3 Write Operations (0% Coverage)

| Operation | Current | Use Case |
|-----------|---------|----------|
| add | ❌ | Create records in NetSuite |
| addList | ❌ | Bulk record creation |
| update | ❌ | Update records in NetSuite |
| updateList | ❌ | Bulk record updates |
| upsert | ❌ | Sync data both ways |
| upsertList | ❌ | Bulk bidirectional sync |
| delete | ❌ | Remove records |
| deleteList | ❌ | Bulk deletions |

**Gap Analysis**:
- Write operations would enable bidirectional sync
- Currently ETL is read-only from NetSuite

### 2.4 Transform Operations (0% Coverage)

| Operation | Current | Use Case |
|-----------|---------|----------|
| transform | ❌ | Quote→Order, Order→Invoice |

**Gap Analysis**:
- Transform enables workflow automation
- Could automate document conversion

### 2.5 Relationship Operations (0% Coverage)

| Operation | Current | Use Case |
|-----------|---------|----------|
| attach | ❌ | Link files to records |
| detach | ❌ | Unlink records |

**Gap Analysis**:
- Lower priority for ETL
- Useful for file management

### 2.6 Async Operations (0% Coverage)

| Operation | Current | Use Case |
|-----------|---------|----------|
| asyncAddList | ❌ | Large batch creates |
| asyncUpdateList | ❌ | Large batch updates |
| asyncUpsertList | ❌ | Large batch upserts |
| asyncDeleteList | ❌ | Large batch deletes |
| getAsyncResult | ❌ | Check async status |

**Gap Analysis**:
- Async operations important for high-volume writes
- Better for bulk data loading

---

## 3. REST API Gap

| Aspect | SOAP (Current) | REST (Available) |
|--------|---------------|------------------|
| Implementation | Yes | No |
| Protocol | XML/SOAP | JSON/REST |
| Modern Records | Some missing | Full support |
| SuiteQL | No | Yes |
| Async | Limited | Full |
| Efficiency | Lower | Higher |

**Gap Analysis**:
- REST API provides access to newer record types
- SuiteQL enables flexible SQL-like queries
- JSON more efficient than XML

---

## 4. Priority Recommendations

### High Priority

| Operation | Reason | Effort |
|-----------|--------|--------|
| add/update/upsert | Enable write-back | Medium |
| SuiteQL (REST) | Flexible queries | Medium |
| Incremental for entities | Better performance | Low |

### Medium Priority

| Operation | Reason | Effort |
|-----------|--------|--------|
| get/getList | Targeted refresh | Low |
| asyncAddList | Bulk writes | Medium |
| transform | Workflow automation | Medium |

### Lower Priority

| Operation | Reason | Effort |
|-----------|--------|--------|
| attach/detach | Specialized use | Low |
| delete | Rare requirement | Low |

---

## 5. Implementation Effort Estimates

### Quick Wins (1-2 days each)

- get/getList operations
- Enable incremental for Customer/Vendor/Contact

### Medium Effort (1-2 weeks each)

- Write operations (add, update, upsert)
- REST API client foundation
- SuiteQL support

### Larger Effort (2-4 weeks)

- Full REST API parity
- Async operations
- Bidirectional sync framework

---

## 6. Feature Comparison: SOAP vs REST

```
Current (SOAP)                    Available (REST)
─────────────────────────────────────────────────────
✅ Basic search                   ✅ Basic search
✅ Advanced search                ✅ Advanced search
✅ Saved search                   ✅ Saved search
✅ Pagination                     ✅ Pagination
✅ Delete tracking                ✅ Delete tracking
❌ SuiteQL                        ✅ SuiteQL
❌ Write operations               ✅ Write operations
❌ Async bulk                     ✅ Async bulk
❌ Revenue records                ✅ Revenue records
❌ Subscription records           ✅ Subscription records
```

---

## 7. Use Case Coverage

### Current Use Cases Supported

| Use Case | Support Level |
|----------|---------------|
| Extract all transactions | Full |
| Extract all items | Full |
| Extract standard records | Full |
| Track deleted records | Full |
| Incremental sync (Txn/Item) | Full |
| Custom records | Partial |

### Use Cases Not Supported

| Use Case | Missing Operations |
|----------|-------------------|
| Create records in NetSuite | add, addList |
| Update records in NetSuite | update, updateList |
| Bidirectional sync | upsert, upsertList |
| Automate workflows | transform |
| Complex queries | SuiteQL |
| High-volume writes | async operations |
