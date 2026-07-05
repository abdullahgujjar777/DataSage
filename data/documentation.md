# DataSage — Auto-Generated Documentation

_Generated: 2026-07-04T11:42:04.208762+00:00_

## returns

**Purpose:** This table records individual product return transactions. It tracks which order and order line item is being returned, the return date, reason, processing status, and the refund amount.

**Columns:**
- `return_id`: Unique identifier for the return record.
- `order_id`: Identifier of the original order linked to this return.
- `order_item_id`: Identifier of the specific order line item that is being returned.
- `return_date`: Date and time when the return was recorded.
- `reason`: Text code describing why the product was returned (e.g., changed_mind, wrong_item, defective).
- `status`: Current processing state of the return (e.g., approved, refunded, pending).
- `refund_amount`: Monetary amount paid back to the customer for the return.

**Relationships:** order_id links to orders.order_id and order_item_id links to order_items.order_item_id.

**Business Value:** Enables analysis of return reasons, volumes, and financial impact of refunds, as well as linking returns back to original orders for customer service follow‑up.

**⚠️ Ambiguity Flags:**
- `refund_amount`: Currency is not indicated in the sample; amount is likely monetary but the unit (e.g., USD) is unclear.
- `status`: Status records return processing state; other tables also have a status column with different value sets, only the word 'refunded' overlaps, which may be coincidental rather than a defined relationship.

## suppliers

**Purpose:** This table stores information about product suppliers. It tracks each supplier's name, country of operation, contact email, and current status.

**Columns:**
- `supplier_id`: Unique identifier for the supplier.
- `supplier_name`: Legal or commercial name of the supplier.
- `country`: Country where the supplier is based.
- `contact_email`: Email address for contacting the supplier.
- `status`: Current activity state of the supplier (sample shows 'active').

**Relationships:** supplier_id is referenced by products.supplier_id.

**Business Value:** Supports reporting on supplier geography, activity status, and enables joins to product data to analyse supplier performance.

**⚠️ Ambiguity Flags:**
- `status`: Status indicates supplier activity, but other tables use a status column for different concepts; overlap is limited to generic words like 'active'.
- `country`: Country lists supplier locations; customers also have a country column for customer residence with different values, and no overlapping values are seen in the samples.

## inventory

**Purpose:** This table keeps a snapshot of stock levels for each product. It records how many units are on hand, the reorder threshold, and when the record was last updated.

**Columns:**
- `inventory_id`: Unique identifier for the inventory record.
- `product_id`: Identifier of the product to which the stock counts belong.
- `quantity_on_hand`: Number of units currently available in inventory.
- `reorder_threshold`: Minimum quantity that triggers a reorder request.
- `last_updated`: Timestamp of the most recent inventory count update.

**Relationships:** product_id links to products.product_id.

**Business Value:** Allows calculation of stock availability, identification of items needing replenishment, and timing of inventory updates.

## marketing_campaigns

**Purpose:** This table logs marketing campaigns run by the company. It tracks each campaign's name, channel, dates, budget, and lifecycle status.

**Columns:**
- `campaign_id`: Unique identifier for the campaign.
- `campaign_name`: Descriptive name of the marketing effort.
- `channel`: Medium used for the campaign (e.g., social_media, affiliate, paid_search).
- `start_date`: Date when the campaign began.
- `end_date`: Date when the campaign ended or null if ongoing.
- `budget`: Planned monetary spend for the campaign.
- `status`: Current lifecycle stage of the campaign (active, completed, paused).

**Relationships:** 

**Business Value:** Enables evaluation of marketing spend effectiveness, channel performance, and campaign timing.

**⚠️ Ambiguity Flags:**
- `channel`: Channel refers to marketing medium; orders also have a channel column for sales channels (in_store, marketplace, etc.) with different values and no overlap.
- `status`: Status indicates campaign lifecycle; other tables use status for unrelated concepts, with only generic words overlapping, so the meaning is likely distinct.

## customers

**Purpose:** This table contains records for each customer. It tracks personal contact details, signup date, country of residence, segment classification, and current activity status.

**Columns:**
- `customer_id`: Unique identifier for the customer.
- `email`: Customer's email address.
- `first_name`: Customer's given name.
- `last_name`: Customer's family name.
- `signup_date`: Date the customer account was created.
- `country`: Country where the customer resides.
- `segment`: Business-assigned group indicating customer value or risk (e.g., new, at_risk, high_value, regular).
- `status`: Current activity state of the customer account (active, inactive, churned).

**Relationships:** 

**Business Value:** Supports segmentation analysis, churn prediction, and geographic distribution of the customer base.

**⚠️ Ambiguity Flags:**
- `status`: Status reflects customer activity; other tables have a status column for different entities, with only generic overlap, suggesting distinct meanings.
- `country`: Country lists customer residency; suppliers also have a country column for supplier location with different values and no overlap in the samples.

## orders

**Purpose:** This table records each purchase order placed by a customer. It tracks the customer, order date, sales channel, current order status, and total monetary amount.

**Columns:**
- `order_id`: Unique identifier for the order.
- `customer_id`: Identifier of the customer who placed the order.
- `order_date`: Timestamp when the order was created.
- `status`: Current fulfillment or financial state of the order (e.g., cancelled, refunded, delivered).
- `channel`: Sales channel through which the order was made (in_store, marketplace, mobile_app, web).
- `total_amount`: Total monetary value of the order.

**Relationships:** customer_id links to customers.customer_id.

**Business Value:** Enables revenue reporting, channel performance analysis, and monitoring of order lifecycle stages.

**⚠️ Ambiguity Flags:**
- `total_amount`: Monetary unit is not specified; assumed to be a currency but the exact type (e.g., USD) is unclear.
- `status`: Status records order fulfillment state; other tables also have a status column with different vocabularies, only generic overlap observed.
- `channel`: Channel indicates sales channel; marketing_campaigns also has a channel column for marketing mediums with different values and no overlap.

## order_items

**Purpose:** This table lists the individual line items that belong to each order. It records which product was sold, the quantity, and the price per unit at the time of sale.

**Columns:**
- `order_item_id`: Unique identifier for the order line item.
- `order_id`: Identifier of the order that contains this line item.
- `product_id`: Identifier of the product being sold.
- `quantity`: Number of units of the product purchased in this line item.
- `unit_price`: Price per single unit of the product for this line item.

**Relationships:** order_id links to orders.order_id and product_id links to products.product_id.

**Business Value:** Supports detailed revenue breakdowns, product popularity tracking, and calculation of average selling price per product.

**⚠️ Ambiguity Flags:**
- `unit_price`: Currency for the unit price is not indicated in the sample data.

## products

**Purpose:** This table catalogs the products that can be sold. It tracks each product's name, category, price, availability status, and its supplier.

**Columns:**
- `product_id`: Unique identifier for the product.
- `product_name`: Descriptive name of the product.
- `category`: Business category or segment the product belongs to (e.g., beauty, toys, home_goods, sports).
- `price`: Standard selling price for the product.
- `status`: Current availability state of the product (active, discontinued, out_of_stock).
- `supplier_id`: Identifier of the supplier that provides this product.

**Relationships:** supplier_id links to suppliers.supplier_id.

**Business Value:** Allows analysis of product pricing, category performance, and supplier contributions to the catalog.

**⚠️ Ambiguity Flags:**
- `price`: Monetary unit is not specified; assumed to be a currency but the exact type is unclear.
- `status`: Status indicates product availability; other tables also have a status column with differing vocabularies, only generic overlap, suggesting separate meanings.
