# Ramp Developer API — Endpoint Cheatsheet

All **246 operations** across **169 paths**, generated from
[`api-docs/developer-api.json`](api-docs/developer-api.json) (OpenAPI 3.0.2, `Ramp Developer API` v1).

> Generated 2026-08-01 by [`api-docs/gen-cheatsheet.py`](api-docs/gen-cheatsheet.py). Do not hand-edit — run `api-docs/refresh.sh` to rebuild.

Base URL: `https://api.ramp.com` · Auth: OAuth 2.0 authorization code · Docs: https://docs.ramp.com/developer-api/v1/introduction

## Before scoping anything against this

- **44 of 246 operations are marked `x-ramp-plus-required`** — they need the Ramp Plus plan. Confirm Affect's plan before designing against them.
- **120 are marked `x-beta`** and 3 are deprecated. Beta endpoints can change without notice; treat them as unsuitable for a production pipeline.
- Every operation requires an OAuth scope (right-hand column). Scopes are granted per app in the Ramp developer console — an app with the wrong scopes gets a 403, not a 401.
- List endpoints paginate with `start` (id cursor) + `page_size` (2–100), not offsets.

**Legend:** `Plus` = requires Ramp Plus · `beta` = unstable · `destructive` = irreversible · **deprecated** = do not build on.

---

## Accounting

_Operations related to accounting_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/accounting/accounts` | List general ledger accounts | — | `accounting:read` |
| `POST /developer/v1/accounting/accounts` | Upload general ledger accounts | — | `accounting:write` |
| `DELETE /developer/v1/accounting/accounts/{gl_account_id}` | Delete a general ledger account | — | `accounting:write` |
| `GET /developer/v1/accounting/accounts/{gl_account_id}` | Fetch a general ledger account | — | `accounting:read` |
| `PATCH /developer/v1/accounting/accounts/{gl_account_id}` | Update a general ledger account | — | `accounting:write` |
| `GET /developer/v1/accounting/all-connections` | Fetch all accounting connections for the current business | — | `accounting:read` |
| `POST /developer/v1/accounting/codings` | Post accounting coding selections to an object | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/connection` | Disconnect an accounting connection | — | `accounting:write` |
| `GET /developer/v1/accounting/connection` | Fetch the current active accounting connection | **deprecated** | `accounting:read` |
| `POST /developer/v1/accounting/connection` | Register a new API based accounting connection | — | `accounting:write` |
| `GET /developer/v1/accounting/connection/{connection_id}` | Fetch an accounting connection by ID | beta | `accounting:read` |
| `PATCH /developer/v1/accounting/connection/{connection_id}` | Update an accounting connection | beta | `accounting:write` |
| `POST /developer/v1/accounting/connection/{connection_id}/reactivate` | Reactivate a previously unlinked accounting connection | — | `accounting:write` |
| `POST /developer/v1/accounting/connection/{connection_id}/ready-to-migrate` | Mark an inactive accounting API based connection as ready to migrate | — | `accounting:write` |
| `POST /developer/v1/accounting/entities` | Upload entities | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/field-option-filter-rules` | Bulk delete field option filter rules | beta | `accounting:write` |
| `GET /developer/v1/accounting/field-option-filter-rules` | List field option filter rules | beta | `accounting:read` |
| `POST /developer/v1/accounting/field-option-filter-rules` | Bulk create field option filter rules | beta | `accounting:write` |
| `GET /developer/v1/accounting/field-options` | List options for a given custom accounting field | — | `accounting:read` |
| `POST /developer/v1/accounting/field-options` | Upload new options | — | `accounting:write` |
| `DELETE /developer/v1/accounting/field-options/{field_option_id}` | Delete a custom accounting field option | — | `accounting:write` |
| `GET /developer/v1/accounting/field-options/{field_option_id}` | Fetch a custom accounting field option | — | `accounting:read` |
| `PATCH /developer/v1/accounting/field-options/{field_option_id}` | Update a custom accounting field option | — | `accounting:write` |
| `PUT /developer/v1/accounting/field-options/{field_option_id}` | Update a custom accounting field option | — | `accounting:write` |
| `GET /developer/v1/accounting/fields` | List custom accounting fields | — | `accounting:read` |
| `POST /developer/v1/accounting/fields` | Create a new custom accounting field | — | `accounting:write` |
| `DELETE /developer/v1/accounting/fields/{field_id}` | Delete a custom accounting field | — | `accounting:write` |
| `GET /developer/v1/accounting/fields/{field_id}` | Fetch a custom accounting field | — | `accounting:read` |
| `PATCH /developer/v1/accounting/fields/{field_id}` | Update a custom accounting field | — | `accounting:write` |
| `DELETE /developer/v1/accounting/inventory-item` | Delete inventory item accounting field | beta | `accounting:write` |
| `GET /developer/v1/accounting/inventory-item` | Fetch inventory item accounting field | beta | `accounting:read` |
| `PATCH /developer/v1/accounting/inventory-item` | Update inventory item accounting field | beta | `accounting:write` |
| `POST /developer/v1/accounting/inventory-item` | Create a new inventory item accounting field | beta | `accounting:write` |
| `GET /developer/v1/accounting/inventory-item/options` | List inventory item options | beta | `accounting:read` |
| `POST /developer/v1/accounting/inventory-item/options` | Upload inventory item options | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/inventory-item/options/{option_id}` | Delete an inventory item option | beta | `accounting:write` |
| `PATCH /developer/v1/accounting/inventory-item/options/{option_id}` | Update an inventory item option | beta | `accounting:write` |
| `POST /developer/v1/accounting/ramp-field-options` | Upload new options for a Ramp-only field | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/ramp-field-options/{field_option_id}` | Delete a Ramp-only field option | beta | `accounting:write` |
| `PATCH /developer/v1/accounting/ramp-field-options/{field_option_id}` | Update a Ramp-only field option | beta | `accounting:write` |
| `GET /developer/v1/accounting/ramp-fields` | List Ramp-only accounting fields | beta | `accounting:read` |
| `POST /developer/v1/accounting/ramp-fields` | Create a Ramp-only accounting field | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/ramp-fields/{field_id}` | Delete a Ramp-only accounting field | beta | `accounting:write` |
| `GET /developer/v1/accounting/ramp-fields/{field_id}` | Fetch a Ramp-only accounting field | beta | `accounting:read` |
| `PATCH /developer/v1/accounting/ramp-fields/{field_id}` | Update a Ramp-only accounting field | beta | `accounting:write` |
| `POST /developer/v1/accounting/ready-to-sync` | Mark objects as ready to sync to your accounting provider | beta | `accounting:write` |
| `POST /developer/v1/accounting/syncs` | Post sync status | — | `accounting:write` |
| `DELETE /developer/v1/accounting/tax/code` | Delete tax code accounting field | beta | `accounting:write` |
| `GET /developer/v1/accounting/tax/code` | Fetch tax code accounting field | beta | `accounting:read` |
| `PATCH /developer/v1/accounting/tax/code` | Update tax code accounting field | beta | `accounting:write` |
| `POST /developer/v1/accounting/tax/code` | Create a new tax code accounting field | beta | `accounting:write` |
| `GET /developer/v1/accounting/tax/code/options` | List tax code options | beta | `accounting:read` |
| `POST /developer/v1/accounting/tax/code/options` | Upload tax code options | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/tax/code/options/{option_id}` | Delete a tax code option | beta | `accounting:write` |
| `PATCH /developer/v1/accounting/tax/code/options/{option_id}` | Update a tax code option | beta | `accounting:write` |
| `GET /developer/v1/accounting/tax/rates` | List tax rates | beta | `accounting:read` |
| `POST /developer/v1/accounting/tax/rates` | Upload tax rates | beta | `accounting:write` |
| `DELETE /developer/v1/accounting/tax/rates/{tax_rate_id}` | Delete a tax rate | beta | `accounting:write` |
| `PATCH /developer/v1/accounting/tax/rates/{tax_rate_id}` | Update a tax rate | beta | `accounting:write` |
| `GET /developer/v1/accounting/vendors` | List vendors | — | `accounting:read` |
| `POST /developer/v1/accounting/vendors` | Upload vendors | — | `accounting:write` |
| `DELETE /developer/v1/accounting/vendors/{vendor_id}` | Delete a vendor | — | `accounting:write` |
| `GET /developer/v1/accounting/vendors/{vendor_id}` | Fetch a vendor | — | `accounting:read` |
| `PATCH /developer/v1/accounting/vendors/{vendor_id}` | Update a vendor | — | `accounting:write` |

## Application

_Operations related to financing applications_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/applications` | Fetch a financing application | beta | `applications:read` |
| `POST /developer/v1/applications` | Create a financing application | beta | — |

## Audit Log

_Operations related to audit log_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/audit-logs/events` | Get audit log events | Plus beta | `audit_logs:read` |

## Bank Accounts

_Operations related to bank accounts_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/bank-accounts` | List bank accounts | — | `bank_accounts:read` |
| `GET /developer/v1/bank-accounts/{bank_account_id}` | Get bank account details | — | `bank_accounts:read` |

## Banking

_Operations related to Banking_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/banking/accounts` | List banking accounts | beta | `treasury:read` |
| `GET /developer/v1/banking/accounts/{account_id}/balance-history` | Get balance history for a banking account | beta | `treasury:read` |
| `GET /developer/v1/banking/syncable-transactions` | List syncable banking transactions | — | `treasury:read` |

## Bill

_Operations related to bill pay_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/bills` | List bills | — | `bills:read` |
| `POST /developer/v1/bills` | Create a bill | — | `bills:write` |
| `GET /developer/v1/bills/drafts` | List draft bills | — | `bills:read` |
| `POST /developer/v1/bills/drafts` | Create a draft bill | beta | `bills:write` |
| `GET /developer/v1/bills/drafts/{draft_bill_id}` | Fetch a draft bill | — | `bills:read` |
| `PATCH /developer/v1/bills/drafts/{draft_bill_id}` | Update a draft bill | beta | `bills:write` |
| `POST /developer/v1/bills/drafts/{draft_bill_id}/attachments` | Upload a file attachment to an existing draft bill | — | `bills:write` |
| `DELETE /developer/v1/bills/{bill_id}` | Archive a bill | — | `bills:write` |
| `GET /developer/v1/bills/{bill_id}` | Fetch a bill | — | `bills:read` |
| `PATCH /developer/v1/bills/{bill_id}` | Update a bill | — | `bills:write` |
| `POST /developer/v1/bills/{bill_id}/attachments` | Upload a file attachment to an existing bill | — | `bills:write` |
| `POST /developer/v1/bills/{bill_id}/hold` | Hold Bill | beta | `bills:write` |
| `POST /developer/v1/bills/{bill_id}/release` | Release Bill Hold | beta | `bills:write` |
| `GET /developer/v1/bills/{bill_id}/remittance-receipt` | Fetch a bill remittance receipt | — | `bills:read` |

## BlankCanvas

_Operations related to blank canvas workflow approvals_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/blank-canvas-approvals/documents` | Upload a document for a blank canvas workflow step | — | `blank_canvas:write` |
| `POST /developer/v1/blank-canvas-approvals/{approval_trigger_instance_id}` | Approve or reject a blank canvas workflow step | — | `blank_canvas:write` |
| `PATCH /developer/v1/blank-canvas-approvals/{approval_trigger_instance_id}/metadata` | Update metadata for a blank canvas external approval request | — | `blank_canvas:write` |

## Business

_Operations related to business_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/business` | Fetch the company information | — | `business:read` |
| `GET /developer/v1/business/balance` | Fetch the company balance information | — | `business:read` |

## Business Entities

_Operations related to entity_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/entities` | List business entities | — | `entities:read` |
| `GET /developer/v1/entities/{entity_id}` | Get a business entity | — | `entities:read` |

## Card Vault

_Operations related to cards in vault_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/vault/cards` | Create a spend limit and retrieve sensitive card details | **deprecated** | `cards:read_vault`<br>`limits:write` |
| `GET /developer/v1/vault/cards/{card_id}` | Fetch a card's sensitive details | **deprecated** | `cards:read_vault` |

## Card Vault Alias

_Operations related to cards in vault_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/cards/vault` | Create a spend limit and retrieve sensitive card details | beta | `cards:read_vault`<br>`limits:write` |
| `GET /developer/v1/cards/vault/{card_id}` | Fetch a card's sensitive details | beta | `cards:read_vault` |

## Cashback

_Operations related to cashback_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/cashbacks` | List cashback payments | — | `cashbacks:read` |
| `GET /developer/v1/cashbacks/{cashback_id}` | Fetch a cashback payment | — | `cashbacks:read` |

## Comments

_Operations related to comments_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/comments/{object_type}/{object_id}` | List comments on an object's discussion thread | beta | — |
| `POST /developer/v1/comments/{object_type}/{object_id}` | Create a comment on an object's discussion thread | beta | — |

## Custom Records

_Operations related to custom records._

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/custom-records/configure/custom-tables` | Create Custom Table | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/configure/custom-tables/{custom_table_name}/columns` | Create Custom Table column | Plus beta | `custom_records:write` |
| `PATCH /developer/v1/custom-records/configure/custom-tables/{custom_table_name}/columns/{column_name}` | Change the API name of a Custom Table's Column | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/configure/native-tables` | Extend Native Ramp table | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/configure/native-tables/{native_table_name}/columns` | Create Native Ramp table field | Plus beta | `custom_records:write` |
| `PATCH /developer/v1/custom-records/configure/native-tables/{native_table_name}/columns/{column_name}` | Change the API name of a Native Table's Custom Record Column | Plus beta | `custom_records:write` |
| `GET /developer/v1/custom-records/custom-tables` | List Custom Tables | Plus beta | `custom_records:read` |
| `GET /developer/v1/custom-records/custom-tables/{custom_table_name}/columns` | List Custom Table columns | Plus beta | `custom_records:read` |
| `DELETE /developer/v1/custom-records/custom-tables/{custom_table_name}/rows` | Delete rows from a Custom Table | Plus beta | `custom_records:write` |
| `GET /developer/v1/custom-records/custom-tables/{custom_table_name}/rows` | List Custom Table rows | Plus beta | `custom_records:read` |
| `PUT /developer/v1/custom-records/custom-tables/{custom_table_name}/rows` | Set values for rows of a Custom Table | Plus beta | `custom_records:write` |
| `PATCH /developer/v1/custom-records/custom-tables/{custom_table_name}/rows/{row_id}` | Change the external key of a Custom Table row | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/custom-tables/{table_name}/rows/-/append` | Append cells to a Custom Table | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/custom-tables/{table_name}/rows/-/remove` | Remove cells from a Custom Table | Plus beta | `custom_records:write` |
| `GET /developer/v1/custom-records/matrix-tables` | List all Matrix tables for the business | Plus beta | `custom_records:read` |
| `POST /developer/v1/custom-records/matrix-tables` | Create a Matrix table | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/matrix-tables/{table_name}/columns` | Add a result column to an existing Matrix table | Plus beta | `custom_records:write` |
| `PATCH /developer/v1/custom-records/matrix-tables/{table_name}/columns/{column_name}` | Change the API name of a Matrix table column (input or result) | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/matrix-tables/{table_name}/list-rows` | List Matrix table rows | Plus beta | `custom_records:read` |
| `POST /developer/v1/custom-records/matrix-tables/{table_name}/rename` | Change the API name of a Matrix table | Plus beta | `custom_records:write` |
| `PUT /developer/v1/custom-records/matrix-tables/{table_name}/rows` | Upsert Matrix table rows | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/matrix-tables/{table_name}/rows/-/append` | Append cells to Matrix table rows | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/matrix-tables/{table_name}/rows/-/remove` | Remove cells from Matrix table rows | Plus beta | `custom_records:write` |
| `DELETE /developer/v1/custom-records/matrix-tables/{table_name}/rows/{row_id}` | Delete a single Matrix table row by ID | Plus beta | `custom_records:write` |
| `GET /developer/v1/custom-records/native-tables` | List Native Ramp tables | Plus beta | `custom_records:read` |
| `GET /developer/v1/custom-records/native-tables/{native_table_name}/columns` | List Custom Columns for a Native Ramp table | Plus beta | `custom_records:read` |
| `GET /developer/v1/custom-records/native-tables/{native_table_name}/rows` | List Custom Column values for rows of a Native Ramp table | Plus beta | `custom_records:read` |
| `PUT /developer/v1/custom-records/native-tables/{native_table_name}/rows` | Set values for rows of a Native Ramp table | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/native-tables/{native_table_name}/rows/-/append` | Append cells to a Native Ramp table | Plus beta | `custom_records:write` |
| `POST /developer/v1/custom-records/native-tables/{native_table_name}/rows/-/remove` | Remove cells from a Native Ramp table | Plus beta | `custom_records:write` |

## CustomForm

_Operations related to custom forms_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/custom-form/collections/responses/{custom_form_collection_response_id}` | Fetch a custom form collection response by ID | — | `custom_forms:read` |

## Department

_Operations related to departments_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/departments` | List departments | — | `departments:read` |
| `POST /developer/v1/departments` | Create a department | — | `departments:write` |
| `GET /developer/v1/departments/{department_id}` | Fetch a department | — | `departments:read` |
| `PATCH /developer/v1/departments/{department_id}` | Update a department | — | `departments:write` |

## Embedded Cards

_Operations related to Embedded Cards_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/embedded/cards/{card_id}/embed` | Create an embed init token for a card | beta | `embedded_cards:write` |

## Fund

_Funds_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/funds` | List funds | beta | `funds:read` |
| `POST /developer/v1/funds` | Create a fund | beta | `funds:write` |
| `DELETE /developer/v1/funds/{fund_id}` | Terminate a fund | beta | `funds:write` |
| `GET /developer/v1/funds/{fund_id}` | Fetch a fund | beta | `funds:read` |
| `PATCH /developer/v1/funds/{fund_id}` | Update a fund | beta | `funds:write` |
| `DELETE /developer/v1/funds/{fund_id}/members` | Remove members from a fund | beta | `funds:write` |
| `POST /developer/v1/funds/{fund_id}/members` | Add members to a fund | beta | `funds:write` |
| `DELETE /developer/v1/funds/{fund_id}/members/{user_id}/suspension` | Unsuspend a fund member | beta | `funds:write` |
| `POST /developer/v1/funds/{fund_id}/members/{user_id}/suspension` | Suspend a fund member | beta | `funds:write` |
| `DELETE /developer/v1/funds/{fund_id}/suspension` | Unsuspend a fund | beta | `funds:write` |
| `POST /developer/v1/funds/{fund_id}/suspension` | Suspend a fund | beta | `funds:write` |

## Item Receipts

_Operations related to item receipts_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/item-receipts` | List item receipts | Plus | `item_receipts:read` |
| `POST /developer/v1/item-receipts` | Create an item receipt | Plus | `item_receipts:write` |
| `DELETE /developer/v1/item-receipts/{item_receipt_id}` | Delete an item receipt | Plus | `item_receipts:write` |
| `GET /developer/v1/item-receipts/{item_receipt_id}` | Fetch an item receipt | Plus | `item_receipts:read` |

## Location

_Operations related to location_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/locations` | List locations | — | `locations:read` |
| `POST /developer/v1/locations` | Create a location | — | `locations:write` |
| `GET /developer/v1/locations/{location_id}` | Fetch a location | — | `locations:read` |
| `PATCH /developer/v1/locations/{location_id}` | Update a location | — | `locations:write` |

## Memo

_Operations related to memos_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/memos` | List memos | — | `memos:read` |
| `GET /developer/v1/memos/{transaction_id}` | Fetch a transaction memo | — | `memos:read` |
| `POST /developer/v1/memos/{transaction_id}` | Upload a new memo for a transaction | — | `memos:write` |

## Merchant

_Operations related to merchant_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/merchants` | List merchants | — | `merchants:read` |

## Physical Card

_Operations related to physical cards_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/cards/physical` | List physical cards | beta | `cards:read` |
| `POST /developer/v1/cards/physical` | Create a physical card | beta | `cards:write` |
| `DELETE /developer/v1/cards/physical/{card_id}` | Terminate a card | beta | `cards:write` |
| `GET /developer/v1/cards/physical/{card_id}` | Fetch a physical card | beta | `cards:read` |
| `PATCH /developer/v1/cards/physical/{card_id}` | Update a physical card | beta | `cards:write` |
| `DELETE /developer/v1/cards/physical/{card_id}/suspension` | Unsuspend a card | beta | `cards:write` |
| `POST /developer/v1/cards/physical/{card_id}/suspension` | Suspend a card | beta | `cards:write` |

## Purchase Order

_Operations related to purchase orders_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/purchase-orders` | List purchase orders | Plus | `purchase_orders:read` |
| `POST /developer/v1/purchase-orders` | Create a purchase order | Plus | `purchase_orders:write` |
| `GET /developer/v1/purchase-orders/{purchase_order_id}` | Fetch a purchase order | Plus | `purchase_orders:read` |
| `PATCH /developer/v1/purchase-orders/{purchase_order_id}` | Update a purchase order | Plus beta | `purchase_orders:write` |
| `POST /developer/v1/purchase-orders/{purchase_order_id}/archive` | Archive a purchase order | Plus | `purchase_orders:write` |
| `POST /developer/v1/purchase-orders/{purchase_order_id}/line-items` | Add line items to an existing purchase order | Plus beta | `purchase_orders:write` |
| `DELETE /developer/v1/purchase-orders/{purchase_order_id}/line-items/{line_item_id}` | Delete a single line item from an existing purchase order | Plus beta | `purchase_orders:write` |
| `PATCH /developer/v1/purchase-orders/{purchase_order_id}/line-items/{line_item_id}` | Update a single line item on an existing purchase order | Plus beta | `purchase_orders:write` |

## Receipt

_Operations related to receipts_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/receipts` | List receipts | — | `receipts:read` |
| `POST /developer/v1/receipts` | Upload a receipt | — | `receipts:write` |
| `GET /developer/v1/receipts/{receipt_id}` | Fetch a receipt | — | `receipts:read` |

## Receipt Integrations

_Operations related to receipt integrations._

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/receipt-integrations/opt-out` | List emails opted out of receipt integrations | — | `receipt_integrations:read` |
| `POST /developer/v1/receipt-integrations/opt-out` | Add a new email to receipt integrations opt-out list | — | `receipt_integrations:write` |
| `DELETE /developer/v1/receipt-integrations/opt-out/{mailbox_opted_out_email_uuid}` | Remove an email from receipt integration opt-out list | — | `receipt_integrations:write` |

## Reimbursement

_Operations related to reimbursements_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/reimbursements` | List reimbursements | — | `reimbursements:read` |
| `POST /developer/v1/reimbursements/mileage` | Create a mileage reimbursement | — | `reimbursements:write` |
| `POST /developer/v1/reimbursements/submit-receipt` | Upload a receipt for a reimbursement | — | `reimbursements:write` |
| `GET /developer/v1/reimbursements/{reimbursement_id}` | Fetch a reimbursement | — | `reimbursements:read` |

## Repayment

_Operations related to repayments_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/repayments` | List repayments | — | `repayments:read` |

## Spend Program

_Spend Program Operations_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/spend-programs` | List spend programs | — | `spend_programs:read` |
| `POST /developer/v1/spend-programs` | Create a spend program | — | `spend_programs:write` |
| `GET /developer/v1/spend-programs/{spend_program_id}` | Fetch a spend program | — | `spend_programs:read` |
| `GET /developer/v1/spend-programs/{spend_program_id}/workflow-nodes` | List External Approval Request nodes for a spend program | — | `spend_programs:read` |

## Spend Request

_Operations related to spend requests_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/spend-requests/draft-via-ocr` | Create a draft spend request via OCR | Plus | `spend_requests:write` |

## Statement

_Operations related to statements_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/statements` | List statements | — | `statements:read` |
| `GET /developer/v1/statements/{statement_id}` | Fetch a statement | — | `statements:read` |

## Token

_Operations related to token_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `POST /developer/v1/token` | Create a token | — | — |
| `POST /developer/v1/token/revoke` | Revoke an access or refresh token | — | — |

## Transaction

_Operations related to transactions_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/transactions` | List transactions | — | `transactions:read` |
| `GET /developer/v1/transactions/{transaction_id}` | Fetch a transaction | — | `transactions:read` |
| `PATCH /developer/v1/transactions/{transaction_id}` | Split a transaction into line items, or update an existing split | beta destructive | `transactions:write` |

## Transfer Payment

_Operations related to transfer payments_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/transfers` | List transfer payments | — | `transfers:read` |
| `GET /developer/v1/transfers/{transfer_id}` | Fetch a transfer payment | — | `transfers:read` |

## Trips

_Operations related to trips and travel_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/trips` | List all trips for the business | — | `trips:read` |
| `GET /developer/v1/trips/{trip_id}` | Fetch a trip | — | `trips:read` |

## Unified Request

_Operations related to unified requests_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/unified-requests` | List unified requests with pagination | — | `unified_requests:read` |
| `GET /developer/v1/unified-requests/{unified_request_id}` | Get details for a specific UnifiedRequest | — | `unified_requests:read` |

## User

_Operations related to users_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/users` | List users | — | `users:read` |
| `POST /developer/v1/users/deferred` | Create a user invite | — | `users:write` |
| `GET /developer/v1/users/deferred/status/{task_id}` | Fetch deferred task status | — | `users:write` |
| `GET /developer/v1/users/{user_id}` | Fetch a user | — | `users:read` |
| `PATCH /developer/v1/users/{user_id}` | Update a user | — | `users:write` |
| `PATCH /developer/v1/users/{user_id}/deactivate` | Deactivate a user | — | `users:write` |
| `POST /developer/v1/users/{user_id}/invite` | Manage a user's invite lifecycle | beta | `users:write` |
| `PATCH /developer/v1/users/{user_id}/reactivate` | Reactivate a user | — | `users:write` |

## Vendor

_Operations related to vendors_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/vendors` | List vendors | — | `vendors:read` |
| `POST /developer/v1/vendors` | Create a new vendor | — | `vendors:write` |
| `POST /developer/v1/vendors/agreements` | List vendor agreements | beta | `vendors:read` |
| `DELETE /developer/v1/vendors/agreements/{agreement_id}` | Delete a vendor agreement | beta | `vendors:write` |
| `GET /developer/v1/vendors/agreements/{agreement_id}` | Fetch a vendor agreement | beta | `vendors:read` |
| `PATCH /developer/v1/vendors/agreements/{agreement_id}` | Update a vendor agreement | beta | `vendors:write` |
| `POST /developer/v1/vendors/agreements/{agreement_id}/documents` | Upload documents for a vendor agreement | beta | `vendors:write` |
| `POST /developer/v1/vendors/agreements/{agreement_id}/link` | Link purchase orders or documents to a vendor agreement | beta | `vendors:write` |
| `POST /developer/v1/vendors/agreements/{agreement_id}/link-spend-request` | Link a spend request to a vendor agreement | beta | `vendors:write` |
| `DELETE /developer/v1/vendors/agreements/{agreement_id}/unlink` | Unlink purchase orders or documents from a vendor agreement | beta | `vendors:write` |
| `GET /developer/v1/vendors/credits` | List all vendor credits for all vendors of a business | beta | `vendors:read` |
| `GET /developer/v1/vendors/credits/{vendor_credit_id}` | Fetch a vendor credit | beta | `vendors:read` |
| `DELETE /developer/v1/vendors/{vendor_id}` | Delete a vendor | — | `vendors:write` |
| `GET /developer/v1/vendors/{vendor_id}` | Fetch a vendor | — | `vendors:read` |
| `PATCH /developer/v1/vendors/{vendor_id}` | Update a vendor | — | `vendors:write` |
| `GET /developer/v1/vendors/{vendor_id}/accounts` | List vendor bank accounts | — | `vendors:read` |
| `GET /developer/v1/vendors/{vendor_id}/accounts/{bank_account_id}` | Fetch a vendor bank account | — | `vendors:read` |
| `POST /developer/v1/vendors/{vendor_id}/accounts/{bank_account_id}/archive` | Archive a vendor bank account | — | `vendors:write` |
| `POST /developer/v1/vendors/{vendor_id}/agreements` | Create a vendor agreement | beta | `vendors:write` |
| `GET /developer/v1/vendors/{vendor_id}/children` | List child vendors of a parent vendor | — | `vendors:read` |
| `GET /developer/v1/vendors/{vendor_id}/contacts` | List vendor contacts for vendor | — | `vendors:read` |
| `GET /developer/v1/vendors/{vendor_id}/contacts/{vendor_contact_id}` | Fetch a vendor contact | — | `vendors:read` |
| `GET /developer/v1/vendors/{vendor_id}/credits` | List vendor credits by vendor | beta | `vendors:read` |
| `POST /developer/v1/vendors/{vendor_id}/hold` | Place a hold on a vendor | beta | `vendors:write` |
| `POST /developer/v1/vendors/{vendor_id}/release` | Release Vendor Hold | beta | `vendors:write` |
| `POST /developer/v1/vendors/{vendor_id}/update-bank-accounts` | Add to a vendor's bank account details | — | `vendors:write` |

## Virtual Cards

_Operations related to virtual cards._

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/cards/virtual` | List virtual cards | beta | `cards:read` |
| `GET /developer/v1/cards/virtual/{card_id}` | Fetch a virtual card | beta | `cards:read` |

## Webhooks

_Subscribe to webhooks through developer API_

| Endpoint | Summary | Flags | Scope |
|---|---|---|---|
| `GET /developer/v1/webhooks` | Get all webhook subscriptions | — | — |
| `POST /developer/v1/webhooks` | Creates a new webhook subscription | — | — |
| `POST /developer/v1/webhooks/mock-webhook-event` | Create a mock webhook event for active subscriptions matching the event type | — | — |
| `DELETE /developer/v1/webhooks/{webhook_id}` | Delete a webhook subscription by id | — | — |
| `GET /developer/v1/webhooks/{webhook_id}` | Get a webhook subscription by id | — | — |
| `POST /developer/v1/webhooks/{webhook_id}/verify` | Verify a webhook subscription | — | — |

---

## Query parameters by endpoint

Only endpoints that declare query parameters in the spec are listed.

| Endpoint | Query parameters |
|---|---|
| `GET /developer/v1/accounting/accounts` | `remote_id`, `is_active`, `code`, `accounting_connection_id`, `start`, `page_size`, `is_synced` |
| `GET /developer/v1/accounting/accounts/{gl_account_id}` | `accounting_connection_id` |
| `GET /developer/v1/accounting/field-option-filter-rules` | `target_field_option_remote_id`, `target_field_remote_id`, `accounting_connection_id`, `start`, `page_size` |
| `GET /developer/v1/accounting/field-options` | `remote_id`, `is_active`, `code`, `visibility`, `accounting_connection_id`, `field_id`, `start`, `page_size` |
| `GET /developer/v1/accounting/field-options/{field_option_id}` | `accounting_connection_id` |
| `GET /developer/v1/accounting/fields` | `remote_id`, `is_active`, `accounting_connection_id`, `start`, `page_size` |
| `GET /developer/v1/accounting/fields/{field_id}` | `accounting_connection_id` |
| `GET /developer/v1/accounting/inventory-item` | `accounting_connection_id` |
| `GET /developer/v1/accounting/inventory-item/options` | `remote_id`, `is_active`, `code`, `accounting_connection_id`, `start`, `page_size`, `is_synced` |
| `GET /developer/v1/accounting/ramp-fields` | `remote_id`, `is_active`, `accounting_connection_id`, `start`, `page_size` |
| `GET /developer/v1/accounting/ramp-fields/{field_id}` | `accounting_connection_id` |
| `GET /developer/v1/accounting/tax/code` | `accounting_connection_id` |
| `GET /developer/v1/accounting/tax/code/options` | `remote_id`, `is_active`, `code`, `accounting_connection_id`, `start`, `page_size`, `is_synced` |
| `GET /developer/v1/accounting/tax/rates` | `accounting_connection_id`, `start`, `page_size` |
| `GET /developer/v1/accounting/vendors` | `remote_id`, `is_active`, `code`, `accounting_connection_id`, `start`, `page_size`, `is_synced` |
| `GET /developer/v1/accounting/vendors/{vendor_id}` | `accounting_connection_id` |
| `GET /developer/v1/audit-logs/events` | `user_ids`, `from_date`, `to_date`, `event_actor_types`, `event_types`, `object_id`, `resource_name`, `start`, `page_size` |
| `GET /developer/v1/bank-accounts` | `connection_provider`, `start`, `page_size` |
| `GET /developer/v1/banking/accounts` | `start`, `page_size` |
| `GET /developer/v1/banking/accounts/{account_id}/balance-history` | `start_date`, `end_date`, `start`, `page_size` |
| `GET /developer/v1/banking/syncable-transactions` | `entity_ids`, `start_date`, `end_date`, `include_synced_transfers`, `start`, `page_size` |
| `GET /developer/v1/bills` | `entity_id`, `customer_friendly_payment_id`, `draft_bill_id`, `invoice_number`, `remote_id`, `accounting_field_selection_id`, `status_summaries`, `payment_id`, `vendor_id`, `is_accounting_sync_enabled`, `approval_status`, `payment_method`, `payment_status`, `sync_status`, `sync_ready`, `payment_details_missing`, `is_archived`, `from_created_at`, `to_created_at`, `from_due_date`, `to_due_date`, `from_issued_date`, `to_issued_date`, `from_paid_at`, `to_paid_at`, `from_payment_date`, `to_payment_date`, `min_amount`, `max_amount`, `start`, `page_size` |
| `GET /developer/v1/bills/drafts` | `entity_id`, `invoice_number`, `remote_id`, `vendor_id`, `from_created_at`, `to_created_at`, `from_due_date`, `to_due_date`, `from_issued_date`, `to_issued_date`, `start`, `page_size` |
| `GET /developer/v1/cards/physical` | `user_id`, `display_name`, `include_activated_only`, `include_terminated_only`, `start`, `page_size` |
| `GET /developer/v1/cards/virtual` | `entity_id`, `user_id`, `is_terminated`, `start`, `page_size` |
| `GET /developer/v1/cashbacks` | `sync_status`, `entity_id`, `statement_id`, `sync_ready`, `from_date`, `to_date`, `start`, `page_size` |
| `GET /developer/v1/comments/{object_type}/{object_id}` | `start`, `page_size` |
| `GET /developer/v1/custom-records/custom-tables/{custom_table_name}/rows` | `external_key`, `include_all_referenced_rows`, `page_size`, `start` |
| `GET /developer/v1/custom-records/native-tables/{native_table_name}/rows` | `include_all_referenced_rows`, `page_size`, `ramp_id`, `start` |
| `GET /developer/v1/departments` | `start`, `page_size` |
| `GET /developer/v1/entities` | `currency`, `entity_name`, `is_primary`, `hide_inactive`, `include_custom_field_values`, `start`, `page_size`, `include_deleted_accounts` |
| `GET /developer/v1/entities/{entity_id}` | `hide_inactive`, `include_custom_field_values` |
| `GET /developer/v1/funds` | `display_name`, `spend_program_id`, `entity_id`, `created_after`, `created_before`, `card_id`, `user_id`, `is_terminated`, `member_roles`, `start`, `page_size` |
| `GET /developer/v1/item-receipts` | `start`, `page_size`, `entity_id`, `purchase_order_line_item_id`, `purchase_order_id`, `include_archived` |
| `GET /developer/v1/locations` | `entity_id`, `start`, `page_size` |
| `GET /developer/v1/memos` | `card_id`, `department_id`, `location_id`, `manager_id`, `merchant_id`, `user_id`, `from_date`, `to_date`, `start`, `page_size` |
| `GET /developer/v1/merchants` | `transaction_from_date`, `transaction_to_date`, `start`, `page_size` |
| `GET /developer/v1/purchase-orders` | `creation_source`, `from_created_at`, `to_created_at`, `external_id`, `remote_id`, `receipt_status`, `start`, `page_size`, `entity_id`, `spend_request_id`, `three_way_match_enabled`, `include_archived` |
| `GET /developer/v1/receipts` | `created_after`, `created_before`, `reimbursement_id`, `transaction_id`, `from_date`, `to_date`, `include_ocr_data`, `start`, `page_size` |
| `GET /developer/v1/receipts/{receipt_id}` | `include_ocr_data` |
| `GET /developer/v1/reimbursements` | `direction`, `state`, `sync_status`, `from_transaction_date`, `to_transaction_date`, `awaiting_approval_by_user_id`, `has_been_approved`, `trip_id`, `accounting_field_selection_id`, `entity_id`, `from_date`, `to_date`, `from_submitted_at`, `to_submitted_at`, `synced_after`, `sync_ready`, `has_no_sync_commits`, `updated_after`, `start`, `page_size`, `user_id` |
| `GET /developer/v1/repayments` | `entity_id`, `funding_methods`, `from_repaid_at`, `to_repaid_at`, `start`, `page_size`, `user_id` |
| `GET /developer/v1/spend-programs` | `start`, `page_size` |
| `GET /developer/v1/spend-programs/{spend_program_id}/workflow-nodes` | `service_key` |
| `GET /developer/v1/statements` | `from_date`, `to_date`, `start`, `page_size` |
| `GET /developer/v1/transactions` | `sk_category_id`, `department_id`, `limit_id`, `location_id`, `merchant_id`, `card_id`, `spend_program_id`, `statement_id`, `approval_status`, `state`, `user_id`, `awaiting_approval_by_user_id`, `sync_status`, `has_been_approved`, `all_requirements_met_and_approved`, `has_statement`, `synced_after`, `min_amount`, `has_no_sync_commits`, `max_amount`, `from_date`, `to_date`, `trip_id`, `accounting_field_selection_id`, `entity_id`, `requires_memo`, `include_merchant_data`, `order_by_date_asc`, `order_by_date_desc`, `order_by_amount_asc`, `order_by_amount_desc`, `start`, `page_size` |
| `GET /developer/v1/transactions/{transaction_id}` | `include_merchant_data` |
| `GET /developer/v1/transfers` | `sync_status`, `status`, `entity_id`, `statement_id`, `has_no_sync_commits`, `from_date`, `to_date`, `start`, `page_size` |
| `GET /developer/v1/trips` | `user_ids`, `status`, `from_date`, `to_date`, `min_amount`, `max_amount`, `trip_name`, `start`, `page_size` |
| `GET /developer/v1/unified-requests` | `department_ids`, `entity_ids`, `location_ids`, `owner_user_ids`, `spend_program_ids`, `spend_request_types`, `request_statuses`, `unified_spend_request_types`, `include_deleted`, `min_amount`, `max_amount`, `from_created_at`, `to_created_at`, `start`, `page_size` |
| `GET /developer/v1/users` | `employee_id`, `role`, `status`, `start`, `page_size`, `entity_id`, `department_id`, `email`, `location_id` |
| `GET /developer/v1/vendors` | `external_vendor_id`, `merchant_id`, `accounting_vendor_remote_ids`, `vendor_tracking_category_option_ids`, `sk_category_ids`, `from_created_at`, `to_created_at`, `from_updated_at`, `to_updated_at`, `start`, `page_size`, `vendor_owner_id`, `include_subsidiary`, `include_draft`, `is_active`, `name` |
| `GET /developer/v1/vendors/credits` | `entity_id`, `from_created_at`, `to_created_at`, `from_accounting_date`, `to_accounting_date`, `include_fully_used`, `start`, `page_size` |
| `GET /developer/v1/vendors/{vendor_id}/accounts` | `start`, `page_size` |
| `GET /developer/v1/vendors/{vendor_id}/children` | `start`, `page_size` |
| `GET /developer/v1/vendors/{vendor_id}/contacts` | `start`, `page_size` |
| `GET /developer/v1/vendors/{vendor_id}/credits` | `entity_id`, `from_created_at`, `to_created_at`, `from_accounting_date`, `to_accounting_date`, `include_fully_used`, `start`, `page_size` |

---

## OAuth scopes

72 scopes are defined. Request only what the integration needs.

| Scope | Description |
|---|---|
| `accounting:read` | Grant read access to accounting |
| `accounting:write` | Grant write access to accounting |
| `ai_spend:read` | Grant read access to ai_spend |
| `ai_usage:write` | Grant write access to ai_usage |
| `applications:read` | Grant read access to applications |
| `applications:write` | Grant write access to applications |
| `attendee_types:read` | Grant read access to attendee_types |
| `attendee_types:write` | Grant write access to attendee_types |
| `audit_logs:read` | Grant read access to audit_logs |
| `bank_accounts:read` | Grant read access to bank_accounts |
| `bank_accounts:write` | Grant write access to bank_accounts |
| `bank_feeds:read` | Grant read access to bank_feeds |
| `bills:read` | Grant read access to bills |
| `bills:write` | Grant write access to bills |
| `blank_canvas:write` | Grant write access to blank_canvas |
| `budgets:read` | Grant read access to budgets |
| `business:read` | Grant read access to business |
| `cards:read` | Grant read access to cards |
| `cards:read_vault` | Grant read_vault access to cards |
| `cards:write` | Grant write access to cards |
| `cashbacks:read` | Grant read access to cashbacks |
| `comments:write` | Grant write access to comments |
| `custom_forms:read` | Grant read access to custom_forms |
| `custom_records:read` | Grant read access to custom_records |
| `custom_records:write` | Grant write access to custom_records |
| `departments:read` | Grant read access to departments |
| `departments:write` | Grant write access to departments |
| `embedded_cards:write` | Grant write access to embedded_cards |
| `entities:read` | Grant read access to entities |
| `external_attendees:read` | Grant read access to external_attendees |
| `external_attendees:write` | Grant write access to external_attendees |
| `funds:read` | Grant read access to funds |
| `funds:write` | Grant write access to funds |
| `incorporation:read` | Grant read access to incorporation |
| `incorporation:write` | Grant write access to incorporation |
| `item_receipts:read` | Grant read access to item_receipts |
| `item_receipts:write` | Grant write access to item_receipts |
| `limits:read` | Grant read access to limits |
| `limits:write` | Grant write access to limits |
| `locations:read` | Grant read access to locations |
| `locations:write` | Grant write access to locations |
| `memos:read` | Grant read access to memos |
| `memos:write` | Grant write access to memos |
| `merchants:read` | Grant read access to merchants |
| `offline_access` | Grant access to offline_access |
| `openid` | Grant access to openid |
| `purchase_orders:read` | Grant read access to purchase_orders |
| `purchase_orders:write` | Grant write access to purchase_orders |
| `receipt_integrations:read` | Grant read access to receipt_integrations |
| `receipt_integrations:write` | Grant write access to receipt_integrations |
| `receipts:read` | Grant read access to receipts |
| `receipts:write` | Grant write access to receipts |
| `reimbursements:read` | Grant read access to reimbursements |
| `reimbursements:write` | Grant write access to reimbursements |
| `repayments:read` | Grant read access to repayments |
| `spend_programs:read` | Grant read access to spend_programs |
| `spend_programs:write` | Grant write access to spend_programs |
| `spend_requests:read` | Grant read access to spend_requests |
| `spend_requests:write` | Grant write access to spend_requests |
| `statements:read` | Grant read access to statements |
| `tasks:read` | Grant read access to tasks |
| `transactions:read` | Grant read access to transactions |
| `transactions:write` | Grant write access to transactions |
| `transfers:read` | Grant read access to transfers |
| `treasury:read` | Grant read access to treasury |
| `trips:read` | Grant read access to trips |
| `unified_requests:read` | Grant read access to unified_requests |
| `users:read` | Grant read access to users |
| `users:write` | Grant write access to users |
| `vendors:read` | Grant read access to vendors |
| `vendors:write` | Grant write access to vendors |
| `x402:write` | Grant write access to x402 |
