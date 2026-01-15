# NetSuite Role Requirements for Connector

This document provides step-by-step instructions for setting up a NetSuite role for the ETL connector.

## 1. Role Setup Overview

### Recommended Approach
Create a dedicated integration role rather than using standard roles to:
- Minimize security exposure
- Control exact permissions needed
- Easily audit API access
- Avoid conflicts with UI-based permissions

---

## 2. Step-by-Step Role Creation

### Step 1: Create New Role

1. Navigate to **Setup > Users/Roles > Manage Roles > New**
2. Enter role details:
   - **Name**: `ETL Integration Role`
   - **ID**: `customrole_etl_integration`
   - **Subsidiary Restrictions**: Set as needed (All or specific)

### Step 2: Enable Web Services

Under the **Permissions** tab > **Setup**:

| Permission | Level |
|------------|-------|
| Web Services | Full |
| Log in using Access Tokens | Full |
| User Access Tokens | Full |

### Step 3: Set Transaction Permissions

Under **Permissions** tab > **Transactions**:

| Permission | Level |
|------------|-------|
| Invoice | View |
| Sales Order | View |
| Cash Sale | View |
| Credit Memo | View |
| Customer Payment | View |
| Customer Deposit | View |
| Customer Refund | View |
| Estimate | View |
| Purchase Order | View |
| Vendor Bill | View |
| Vendor Credit | View |
| Vendor Payment | View |
| Item Receipt | View |
| Item Fulfillment | View |
| Check | View |
| Deposit | View |
| Journal Entry | View |
| Work Order | View |
| Transfer Order | View |
| Inventory Adjustment | View |
| Expense Report | View |
| Return Authorization | View |

### Step 4: Set Entity Permissions

Under **Permissions** tab > **Lists**:

| Permission | Level |
|------------|-------|
| Customers | View |
| Vendors | View |
| Employees | View |
| Contacts | View |
| Partners | View |
| Jobs | View |
| Items | View |
| Accounts | View |
| Departments | View |
| Locations | View |
| Subsidiaries | View |
| Classes | View |
| Terms | View |
| Currencies | View |
| Tax Codes | View |

### Step 5: Set Custom Record Permissions

For each custom record type:

1. Navigate to **Customization > Custom Record Types**
2. Edit each custom record
3. Go to **Permissions** subtab
4. Add the integration role with **View** level

### Step 6: Enable Deleted Records Tracking

Under **Permissions** tab > **Setup**:

| Permission | Level |
|------------|-------|
| Deleted Records | View |

---

## 3. Create Integration User

### Step 1: Create User

1. Navigate to **Setup > Users/Roles > Manage Users > New**
2. Fill in required fields:
   - **Name**: `API Integration User`
   - **Email**: `integration@yourcompany.com`
   - **Give Access**: Yes
   - **Role**: Select `ETL Integration Role`

### Step 2: Generate Access Tokens

1. Navigate to **Setup > Users/Roles > Access Tokens > New**
2. Select:
   - **Application**: Your integration record
   - **User**: `API Integration User`
   - **Role**: `ETL Integration Role`
3. Save and record the Token ID and Token Secret

---

## 4. Integration Record Setup

### Create Integration Record

1. Navigate to **Setup > Integration > Manage Integrations > New**
2. Configure:
   - **Name**: `ETL Connector Integration`
   - **State**: Enabled
   - **Token-Based Authentication**: Yes (TBA)
   - **User Credentials**: No (use TBA instead)

### Record Credentials

Save these values for connector configuration:
- Consumer Key
- Consumer Secret
- Token ID (from access token)
- Token Secret (from access token)
- Account ID

---

## 5. Permission Verification

### Test API Access

Use this SOAP request to verify permissions:

```xml
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:ns="urn:messages_2022_1.platform.webservices.netsuite.com">
  <soap:Body>
    <ns:search>
      <ns:searchRecord xsi:type="CustomerSearchBasic">
        <ns:internalId operator="anyOf">
          <ns:searchValue internalId="1"/>
        </ns:internalId>
      </ns:searchRecord>
    </ns:search>
  </soap:Body>
</soap:Envelope>
```

### Check for Permission Errors

Common error responses:
- `INSUFFICIENT_PERMISSION` - Missing record permission
- `SSS_INVALID_WS_OPER` - Web services not enabled
- `INVALID_LOGIN` - Token or credentials issue

---

## 6. Subsidiary Configuration (OneWorld)

### Single Subsidiary Access

If restricting to specific subsidiaries:

1. Edit the role
2. Under **Subsidiary Restrictions**:
   - Select **Restrict access to specific subsidiaries**
   - Choose applicable subsidiaries
   - Check **Include children** if needed

### Cross-Subsidiary Access

For full access across all subsidiaries:

1. Under **Subsidiary Restrictions**:
   - Select **No restrictions**

---

## 7. Audit and Monitoring

### Enable Login Audit Trail

1. Navigate to **Setup > Company > Enable Features**
2. Under **SuiteCloud** tab:
   - Enable **Web Services**
   - Enable **Token-Based Authentication**

### Monitor API Usage

1. Navigate to **Setup > Integration > Web Services Usage Log**
2. Filter by integration user
3. Review operation counts and errors

---

## 8. Security Best Practices

### Token Management
- Rotate tokens periodically
- Use separate tokens for dev/test/prod
- Never share tokens across environments

### Role Isolation
- Create dedicated role for integration
- Don't grant UI permissions to API users
- Minimize permission levels (View only for ETL)

### IP Restrictions (Optional)
- Navigate to **Setup > Integration > Web Services Preferences**
- Add IP restrictions for the integration

---

## 9. Quick Reference Card

```
ETL Connector Role Setup Checklist:
□ Create role: ETL Integration Role
□ Enable Web Services permission
□ Enable Token-Based Auth permission
□ Set View for all transaction types
□ Set View for all entity types  
□ Set View for all item types
□ Set View for setup records
□ Enable Deleted Records access
□ Configure custom record permissions
□ Create integration user
□ Create integration record
□ Generate access tokens
□ Test API connectivity
□ Document credentials securely
```
