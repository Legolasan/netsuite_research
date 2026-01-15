# NetSuite Objects Catalog

This document provides a comprehensive catalog of all NetSuite objects supported by the connector, organized by category.

## Summary

| Category | Count | Replication Mode | Incremental Support |
|----------|-------|------------------|---------------------|
| Transaction | 37 | Incremental | Yes (lastModifiedDate) |
| Item | 24 | Incremental | Yes (lastModifiedDate) |
| Standard Full Load | 67 | Full Load | Partial (17 have incremental fields) |
| Custom Record | Dynamic | Full Load | No |
| Custom Transaction | Dynamic | Full Load | No |
| Delete Tracking | All | Incremental | Yes (deletedDate) |

**Total Objects: 128+ (plus dynamic custom records)**

---

## 1. Transaction Objects (37 types)

Transactions support **incremental replication** using the `lastModifiedDate` field.

| Object Name | Java Class | Search Class | Status |
|-------------|------------|--------------|--------|
| AssemblyBuild | AssemblyBuild | TransactionSearchBasic | Implemented |
| AssemblyUnbuild | AssemblyUnbuild | TransactionSearchBasic | Implemented |
| BinTransfer | BinTransfer | TransactionSearchBasic | Implemented |
| BinWorksheet | BinWorksheet | TransactionSearchBasic | Implemented |
| CashRefund | CashRefund | TransactionSearchBasic | Implemented |
| CashSale | CashSale | TransactionSearchBasic | Implemented |
| Check | Check | TransactionSearchBasic | Implemented |
| CreditMemo | CreditMemo | TransactionSearchBasic | Implemented |
| CustomerDeposit | CustomerDeposit | TransactionSearchBasic | Implemented |
| CustomerPayment | CustomerPayment | TransactionSearchBasic | Implemented |
| CustomerRefund | CustomerRefund | TransactionSearchBasic | Implemented |
| Deposit | Deposit | TransactionSearchBasic | Implemented |
| DepositApplication | DepositApplication | TransactionSearchBasic | Implemented |
| Estimate | Estimate | TransactionSearchBasic | Implemented |
| ExpenseReport | ExpenseReport | TransactionSearchBasic | Implemented |
| InterCompanyJournalEntry | InterCompanyJournalEntry | TransactionSearchBasic | Implemented |
| InventoryAdjustment | InventoryAdjustment | TransactionSearchBasic | Implemented |
| InventoryCostRevaluation | InventoryCostRevaluation | TransactionSearchBasic | Implemented |
| InventoryTransfer | InventoryTransfer | TransactionSearchBasic | Implemented |
| Invoice | Invoice | TransactionSearchBasic | Implemented |
| ItemFulfillment | ItemFulfillment | TransactionSearchBasic | Implemented |
| ItemReceipt | ItemReceipt | TransactionSearchBasic | Implemented |
| JournalEntry | JournalEntry | TransactionSearchBasic | Implemented |
| PaycheckJournal | PaycheckJournal | TransactionSearchBasic | Implemented |
| PurchaseOrder | PurchaseOrder | TransactionSearchBasic | Implemented |
| ReturnAuthorization | ReturnAuthorization | TransactionSearchBasic | Implemented |
| SalesOrder | SalesOrder | TransactionSearchBasic | Implemented |
| StatisticalJournalEntry | StatisticalJournalEntry | TransactionSearchBasic | Implemented |
| TransferOrder | TransferOrder | TransactionSearchBasic | Implemented |
| VendorBill | VendorBill | TransactionSearchBasic | Implemented |
| VendorCredit | VendorCredit | TransactionSearchBasic | Implemented |
| VendorPayment | VendorPayment | TransactionSearchBasic | Implemented |
| VendorReturnAuthorization | VendorReturnAuthorization | TransactionSearchBasic | Implemented |
| WorkOrder | WorkOrder | TransactionSearchBasic | Implemented |
| WorkOrderClose | WorkOrderClose | TransactionSearchBasic | Implemented |
| WorkOrderCompletion | WorkOrderCompletion | TransactionSearchBasic | Implemented |
| WorkOrderIssue | WorkOrderIssue | TransactionSearchBasic | Implemented |

### Transaction Primary Keys
- `internalId`
- `_type` (discriminator for polymorphic transactions)

---

## 2. Item Objects (24 types)

Items support **incremental replication** using the `lastModifiedDate` field.

| Object Name | Java Class | Search Class | Status |
|-------------|------------|--------------|--------|
| AssemblyItem | AssemblyItem | ItemSearchBasic | Implemented |
| DescriptionItem | DescriptionItem | ItemSearchBasic | Implemented |
| DiscountItem | DiscountItem | ItemSearchBasic | Implemented |
| DownloadItem | DownloadItem | ItemSearchBasic | Implemented |
| GiftCertificateItem | GiftCertificateItem | ItemSearchBasic | Implemented |
| InventoryItem | InventoryItem | ItemSearchBasic | Implemented |
| ItemGroup | ItemGroup | ItemSearchBasic | Implemented |
| KitItem | KitItem | ItemSearchBasic | Implemented |
| LotNumberedAssemblyItem | LotNumberedAssemblyItem | ItemSearchBasic | Implemented |
| LotNumberedInventoryItem | LotNumberedInventoryItem | ItemSearchBasic | Implemented |
| MarkupItem | MarkupItem | ItemSearchBasic | Implemented |
| NonInventoryPurchaseItem | NonInventoryPurchaseItem | ItemSearchBasic | Implemented |
| NonInventoryResaleItem | NonInventoryResaleItem | ItemSearchBasic | Implemented |
| NonInventorySaleItem | NonInventorySaleItem | ItemSearchBasic | Implemented |
| OtherChargePurchaseItem | OtherChargePurchaseItem | ItemSearchBasic | Implemented |
| OtherChargeResaleItem | OtherChargeResaleItem | ItemSearchBasic | Implemented |
| OtherChargeSaleItem | OtherChargeSaleItem | ItemSearchBasic | Implemented |
| PaymentItem | PaymentItem | ItemSearchBasic | Implemented |
| SerializedAssemblyItem | SerializedAssemblyItem | ItemSearchBasic | Implemented |
| SerializedInventoryItem | SerializedInventoryItem | ItemSearchBasic | Implemented |
| ServicePurchaseItem | ServicePurchaseItem | ItemSearchBasic | Implemented |
| ServiceResaleItem | ServiceResaleItem | ItemSearchBasic | Implemented |
| ServiceSaleItem | ServiceSaleItem | ItemSearchBasic | Implemented |
| SubtotalItem | SubtotalItem | ItemSearchBasic | Implemented |

### Item Primary Keys
- `internalId`
- `_type` (discriminator for polymorphic items)

---

## 3. Standard Full Load Objects (67 types)

These objects use **full load replication** (complete refresh each sync).

### 3.1 Objects WITHOUT Incremental Support (50 types)

| Object Name | Java Class | Search Class |
|-------------|------------|--------------|
| Account | Account | AccountSearchBasic |
| AccountingPeriod | AccountingPeriod | AccountingPeriodSearchBasic |
| Address | Address | AddressSearchBasic |
| BillingAccount | BillingAccount | BillingAccountSearchBasic |
| BillingSchedule | BillingSchedule | BillingScheduleSearchBasic |
| Bin | Bin | BinSearchBasic |
| Budget | Budget | BudgetSearchBasic |
| Campaign | Campaign | CampaignSearchBasic |
| Charge | Charge | ChargeSearchBasic |
| Classification | Classification | ClassificationSearchBasic |
| ConsolidatedExchangeRate | ConsolidatedExchangeRate | ConsolidatedExchangeRateSearchBasic |
| ContactCategory | ContactCategory | ContactCategorySearchBasic |
| ContactRole | ContactRole | ContactRoleSearchBasic |
| CostCategory | CostCategory | CostCategorySearchBasic |
| CouponCode | CouponCode | CouponCodeSearchBasic |
| CurrencyRate | CurrencyRate | CurrencyRateSearchBasic |
| CustomerCategory | CustomerCategory | CustomerCategorySearchBasic |
| CustomerMessage | CustomerMessage | CustomerMessageSearchBasic |
| CustomerStatus | CustomerStatus | CustomerStatusSearchBasic |
| CustomList | CustomList | CustomListSearchBasic |
| Department | Department | DepartmentSearchBasic |
| EntityGroup | EntityGroup | EntityGroupSearchBasic |
| ExpenseCategory | ExpenseCategory | ExpenseCategorySearchBasic |
| FairValuePrice | FairValuePrice | FairValuePriceSearchBasic |
| Folder | Folder | FolderSearchBasic |
| GlobalAccountMapping | GlobalAccountMapping | GlobalAccountMappingSearchBasic |
| HcmJob | HcmJob | HcmJobSearchBasic |
| InboundShipment | InboundShipment | InboundShipmentSearchBasic |
| InventoryNumber | InventoryNumber | InventoryNumberSearchBasic |
| ItemAccountMapping | ItemAccountMapping | ItemAccountMappingSearchBasic |
| ItemDemandPlan | ItemDemandPlan | ItemDemandPlanSearchBasic |
| ItemRevision | ItemRevision | ItemRevisionSearchBasic |
| ItemSupplyPlan | ItemSupplyPlan | ItemSupplyPlanSearchBasic |
| Job | Job | JobSearchBasic |
| JobStatus | JobStatus | JobStatusSearchBasic |
| JobType | JobType | JobTypeSearchBasic |
| Location | Location | LocationSearchBasic |
| ManufacturingCostTemplate | ManufacturingCostTemplate | ManufacturingCostTemplateSearchBasic |
| ManufacturingOperationTask | ManufacturingOperationTask | ManufacturingOperationTaskSearchBasic |
| ManufacturingRouting | ManufacturingRouting | ManufacturingRoutingSearchBasic |
| Nexus | Nexus | NexusSearchBasic |
| NoteType | NoteType | NoteTypeSearchBasic |
| Opportunity | Opportunity | OpportunitySearchBasic |
| OtherNameCategory | OtherNameCategory | OtherNameCategorySearchBasic |
| PartnerCategory | PartnerCategory | PartnerCategorySearchBasic |
| PaymentMethod | PaymentMethod | PaymentMethodSearchBasic |
| PayrollItem | PayrollItem | PayrollItemSearchBasic |
| PriceLevel | PriceLevel | PriceLevelSearchBasic |
| PricingGroup | PricingGroup | PricingGroupSearchBasic |
| ProjectTask | ProjectTask | ProjectTaskSearchBasic |
| PromotionCode | PromotionCode | PromotionCodeSearchBasic |
| ResourceAllocation | ResourceAllocation | ResourceAllocationSearchBasic |
| RevRecSchedule | RevRecSchedule | RevRecScheduleSearchBasic |
| RevRecTemplate | RevRecTemplate | RevRecTemplateSearchBasic |
| SalesRole | SalesRole | SalesRoleSearchBasic |
| SalesTaxItem | SalesTaxItem | SalesTaxItemSearchBasic |
| SiteCategory | SiteCategory | SiteCategorySearchBasic |
| Subsidiary | Subsidiary | SubsidiarySearchBasic |
| Task | Task | TaskSearchBasic |
| TaxGroup | TaxGroup | TaxGroupSearchBasic |
| TaxType | TaxType | TaxTypeSearchBasic |
| Term | Term | TermSearchBasic |
| TimeSheet | TimeSheet | TimeSheetSearchBasic |
| Topic | Topic | TopicSearchBasic |
| UnitsType | UnitsType | UnitsTypeSearchBasic |
| Usage | Usage | UsageSearchBasic |
| VendorCategory | VendorCategory | VendorCategorySearchBasic |
| WinLossReason | WinLossReason | WinLossReasonSearchBasic |

### 3.2 Objects WITH Incremental Attribute Support (17 types)

These objects have `lastModifiedDate` fields available but are currently implemented as full load:

| Object Name | Incremental Field | Potential Improvement |
|-------------|-------------------|----------------------|
| CalendarEvent | lastModifiedDate | Enable incremental sync |
| Contact | lastModifiedDate | Enable incremental sync |
| Customer | lastModifiedDate | Enable incremental sync |
| Employee | lastModifiedDate | Enable incremental sync |
| File | lastModifiedDate | Enable incremental sync |
| GiftCertificate | lastModifiedDate | Enable incremental sync |
| Issue | lastModifiedDate | Enable incremental sync |
| Message | lastModifiedDate | Enable incremental sync |
| Note | lastModifiedDate | Enable incremental sync |
| Partner | lastModifiedDate | Enable incremental sync |
| Paycheck | lastModifiedDate | Enable incremental sync |
| PhoneCall | lastModifiedDate | Enable incremental sync |
| Solution | lastModifiedDate | Enable incremental sync |
| SupportCase | lastModifiedDate | Enable incremental sync |
| TimeBill | lastModifiedDate | Enable incremental sync |
| TimeEntry | lastModifiedDate | Enable incremental sync |
| Vendor | lastModifiedDate | Enable incremental sync |

---

## 4. Custom Objects

### 4.1 Custom Record
- **Description**: User-defined record types created in NetSuite customization
- **Search Class**: CustomRecordSearchBasic
- **Replication**: Full Load
- **Dynamic Discovery**: Yes (script IDs discovered at runtime)

### 4.2 Custom Transaction
- **Description**: User-defined transaction types
- **Search Class**: CustomRecordSearchBasic
- **Replication**: Full Load
- **Dynamic Discovery**: Yes

---

## 5. Delete Tracking

| Object Name | Category | Incremental Field |
|-------------|----------|-------------------|
| Delete | DELETE | deletedDate |

Delete tracking supports incremental sync using `deletedDate` to capture deleted records across all supported record types.

---

## SDK Version

- **API Version**: v2022_1
- **Protocol**: SOAP (SuiteTalk)
- **Package**: `com.netsuite.suitetalk.proxy.v2022_1`

---

## Source Files

| File | Description |
|------|-------------|
| `NetsuiteSourceObjectType.java` | Main enum defining all source objects |
| `NetsuiteTransactionRecordType.java` | Transaction type definitions |
| `NetsuiteItemRecordType.java` | Item type definitions |
| `NetsuiteStandardFullLoadRecordType.java` | Standard full load type definitions |
