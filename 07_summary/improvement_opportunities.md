# NetSuite Connector Improvement Opportunities

This document outlines prioritized improvement opportunities for the NetSuite connector.

## 1. Priority Matrix

| Priority | Category | Effort | Impact | Timeline |
|----------|----------|--------|--------|----------|
| P1 | Incremental for Entities | Low | High | 1-2 weeks |
| P1 | SDK Upgrade | Medium | Medium | 2-3 weeks |
| P2 | Write Operations | Medium | High | 3-4 weeks |
| P2 | REST API Support | High | High | 4-6 weeks |
| P3 | SuiteQL Support | Medium | Medium | 2-3 weeks |
| P3 | Async Operations | High | Medium | 4-6 weeks |

---

## 2. P1: Quick Wins

### 2.1 Enable Incremental Sync for Entities

**Current State**: Customer, Vendor, Contact, Employee sync as full load
**Proposed**: Enable incremental using existing lastModifiedDate field

**Impact**:
- 50-90% reduction in API calls for entity syncs
- Faster sync times for large datasets
- Lower governance unit consumption

**Implementation**:
```java
// Change CategoryType from TABLE_OR_REPORT_TYPE to include HISTORICAL_TABLE_TYPE
CUSTOMER(
    "Customer",
    NetsuiteRecordCategoryType.STANDARD_FULL_LOAD, // Change to new incremental category
    EnumSet.of(CategoryType.HISTORICAL_TABLE_TYPE, CategoryType.TABLE_OR_REPORT_TYPE),
    new CustomerInternalSearch())
```

**Files to Modify**:
- `NetsuiteSourceObjectType.java`
- Related InternalSearch classes

### 2.2 SDK Version Upgrade

**Current**: v2022_1
**Target**: v2024_1

**Benefits**:
- Access to newer record types
- Bug fixes and improvements
- Better API coverage

**Effort**: Medium (requires testing all object types)

---

## 3. P2: High Value Enhancements

### 3.1 Write Operations

**Operations to Add**:
- `add` / `addList`
- `update` / `updateList`
- `upsert` / `upsertList`

**Benefits**:
- Enable bidirectional sync
- Support data push to NetSuite
- Automate data entry workflows

**Architecture Change**:
```
Current:  NetSuite → Connector → Destination (Read Only)
Proposed: NetSuite ↔ Connector ↔ Destination (Bidirectional)
```

### 3.2 REST API Integration

**Approach**: Add REST client alongside existing SOAP

**Benefits**:
- Access to REST-only records (Revenue, Subscription)
- SuiteQL support
- Async operations
- More efficient JSON payloads

**Key Endpoints**:
```
/services/rest/record/v1/{type}     - CRUD operations
/services/rest/query/v1/suiteql    - SQL-like queries
```

---

## 4. P3: Advanced Features

### 4.1 SuiteQL Support

**What**: SQL-like query language via REST API

**Example**:
```sql
SELECT id, companyname, email, lastmodifieddate
FROM customer
WHERE lastmodifieddate >= TO_DATE('2026-01-01', 'YYYY-MM-DD')
ORDER BY lastmodifieddate
```

**Benefits**:
- More flexible filtering
- Join capabilities
- Aggregation support
- Better performance for complex queries

### 4.2 Async Operations

**Operations**:
- `asyncAddList`
- `asyncUpdateList`
- `asyncUpsertList`

**Benefits**:
- Process large batches efficiently
- Non-blocking execution
- Better for high-volume writes

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)

```
Week 1-2: Enable incremental for entities
├── Customer (High priority)
├── Vendor (High priority)
├── Contact (High priority)
└── Employee (Medium priority)

Week 3-4: SDK upgrade
├── Update dependencies
├── Test all object types
└── Document changes
```

### Phase 2: Write Support (Weeks 5-8)

```
Week 5-6: Core write operations
├── Add operation implementation
├── Update operation implementation
└── Upsert operation implementation

Week 7-8: Testing and refinement
├── Error handling
├── Retry logic
└── Validation
```

### Phase 3: REST Integration (Weeks 9-14)

```
Week 9-10: REST client foundation
├── OAuth2 support
├── HTTP client
└── Error handling

Week 11-12: SuiteQL implementation
├── Query builder
├── Result parsing
└── Pagination

Week 13-14: REST-only objects
├── Revenue records
├── Subscription records
└── Testing
```

---

## 6. Effort Estimates

### Low Effort (1-5 days)

| Task | Days |
|------|------|
| Enable incremental for Customer | 2 |
| Enable incremental for Vendor | 2 |
| Enable incremental for Contact | 2 |
| Add `get` operation | 3 |
| Add `getList` operation | 3 |

### Medium Effort (1-2 weeks)

| Task | Days |
|------|------|
| SDK upgrade | 10 |
| `add` operation | 5 |
| `update` operation | 5 |
| SuiteQL basic support | 7 |

### High Effort (3+ weeks)

| Task | Weeks |
|------|-------|
| Full REST API client | 4 |
| Async operations | 4 |
| Bidirectional sync framework | 6 |

---

## 7. Risk Assessment

### Low Risk

| Improvement | Risk | Mitigation |
|-------------|------|------------|
| Incremental for entities | Code change only | Thorough testing |
| get/getList operations | Additive | Feature flag |

### Medium Risk

| Improvement | Risk | Mitigation |
|-------------|------|------------|
| SDK upgrade | Breaking changes | Version testing |
| Write operations | Data integrity | Validation layer |

### Higher Risk

| Improvement | Risk | Mitigation |
|-------------|------|------------|
| REST API | New protocol | Gradual rollout |
| Async operations | Complexity | Careful design |

---

## 8. Success Metrics

### Performance Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Customer sync time | 10 min (full) | 1 min (incr) |
| API calls per sync | 100+ | 20- |
| Governance units | High | -50% |

### Feature Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Operation coverage | 18% | 60%+ |
| Object coverage | 80% | 95%+ |
| API protocol | SOAP only | SOAP + REST |

---

## 9. Recommendations

### Immediate Actions (Next Sprint)

1. **Enable incremental for Customer/Vendor/Contact**
   - Highest ROI, lowest effort
   - Immediate performance benefits

2. **Plan SDK upgrade**
   - Create test plan
   - Identify breaking changes

### Near-term (Next Quarter)

3. **Implement write operations**
   - Start with `add` and `update`
   - Enable bidirectional use cases

4. **Begin REST API design**
   - Architecture planning
   - OAuth2 implementation

### Long-term (Next 6 Months)

5. **Complete REST integration**
   - SuiteQL support
   - REST-only objects

6. **Async operations**
   - Bulk processing
   - High-volume support
