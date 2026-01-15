# NetSuite Connector Implementation Status

## Executive Summary

The current NetSuite connector provides robust **read-only** data extraction capabilities via the SOAP API. It supports 128+ objects across transactions, items, and standard records with both incremental and full load synchronization.

### Quick Stats

| Metric | Value |
|--------|-------|
| Total Objects | 128+ |
| Transaction Types | 37 |
| Item Types | 24 |
| Standard Records | 67+ |
| API Protocol | SOAP (SuiteTalk v2022_1) |
| Authentication | OAuth1 Token-Based |
| Replication Modes | Incremental + Full Load |

---

## 1. Current Capabilities

### 1.1 Data Extraction

| Capability | Status | Details |
|------------|--------|---------|
| Transaction Sync | ✅ Full | 37 types, incremental |
| Item Sync | ✅ Full | 24 types, incremental |
| Standard Records | ✅ Full | 67 types, full load |
| Custom Records | ✅ Partial | Full load only |
| Delete Tracking | ✅ Full | Incremental |

### 1.2 Search Modes

| Mode | Status | Use Case |
|------|--------|----------|
| Basic Search | ✅ | Standard filtering |
| Saved Search | ✅ | Pre-defined queries |
| Advanced Search | ✅ | Column selection |

### 1.3 Replication

| Mode | Objects | Offset Field |
|------|---------|--------------|
| Incremental | Transaction, Item, Delete | lastModifiedDate |
| Full Load | Standard Records, Custom | None |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    NetSuite Connector                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Client    │  │  Connector  │  │   Service   │         │
│  │  (OAuth1)   │──│   (Core)    │──│  (Search)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         │                │                │                  │
│         │                │                │                  │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐         │
│  │  Record     │  │   Search    │  │   Field     │         │
│  │  Types      │  │   Classes   │  │   Mapping   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Key Components

### 3.1 Record Type Enums

| File | Purpose |
|------|---------|
| `NetsuiteSourceObjectType` | All source objects |
| `NetsuiteTransactionRecordType` | Transaction types |
| `NetsuiteItemRecordType` | Item types |
| `NetsuiteStandardFullLoadRecordType` | Standard records |

### 3.2 Search Implementations

| Pattern | Description |
|---------|-------------|
| `*InternalSearch` | Custom search builders per object |
| Offset Management | Historical/Incremental offset tracking |
| Pagination | SearchMoreWithId pattern |

### 3.3 Client Layer

| Component | Responsibility |
|-----------|---------------|
| `NetsuiteClient` | Core SOAP client |
| `NetsuiteOauth1Client` | OAuth1 authentication |
| `NetsuiteClientProxy` | Request/response handling |

---

## 4. Data Flow

```
1. Schedule Trigger
       ↓
2. Load Last Offset
       ↓
3. Build Search Query (with date filter if incremental)
       ↓
4. Execute Search via SOAP
       ↓
5. Process Records (extract, transform)
       ↓
6. Paginate (searchMoreWithId)
       ↓
7. Update Offset
       ↓
8. Write to Destination
```

---

## 5. Performance Characteristics

### 5.1 Typical Sync Times

| Object Type | Records | Approx Time |
|-------------|---------|-------------|
| Transactions (incremental) | 1000 | 1-2 min |
| Items (incremental) | 1000 | 1-2 min |
| Customer (full load) | 10000 | 5-10 min |
| Reference data | 100-500 | < 1 min |

### 5.2 Governance Usage

| Operation | Units/Call | Typical Volume |
|-----------|------------|----------------|
| Search | 10 | 1-10 per object |
| Pagination | 10 | 1-5 per search |
| GetDeleted | 10 | 1 per sync |

---

## 6. Known Limitations

### 6.1 Functional

| Limitation | Impact | Workaround |
|------------|--------|------------|
| No write operations | Read-only | N/A |
| No REST API | Missing newer objects | N/A |
| No SuiteQL | Limited query flexibility | Use saved searches |

### 6.2 Performance

| Limitation | Impact | Workaround |
|------------|--------|------------|
| 17 entities as full load | Extra API calls | Could be incremental |
| No async operations | Sequential processing | Parallel threads |

---

## 7. Maintenance Notes

### 7.1 SDK Updates

Current SDK: `v2022_1`
Latest Available: `v2024_1`

To upgrade:
1. Download new SDK from NetSuite
2. Update package references
3. Review deprecated/new record types
4. Test all object syncs

### 7.2 Adding New Objects

1. Add to appropriate RecordType enum
2. Create InternalSearch class
3. Add to SourceObjectType
4. Define field mappings
5. Test sync operations
