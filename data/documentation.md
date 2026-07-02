# DataSage — Auto-Generated Documentation

_Generated: 2026-07-02T06:27:43.405814+00:00_

## marketing_campaigns

**Purpose:** This table records marketing campaign details. It tracks each campaign's name, channel, start and end dates, budget, and current status such as active, paused, or completed.

**Columns:**
- `campaign_id`: Unique identifier for the campaign.
- `campaign_name`: Descriptive title of the campaign.
- `channel`: Medium used for the campaign, e.g., social_media, affiliate, paid_search.
- `start_date`: Date the campaign began.
- `end_date`: Date the campaign ended; may be null for ongoing campaigns.
- `budget`: Allocated amount of money for the campaign, shown with two decimal places.
- `status`: Current lifecycle stage of the campaign, such as active, paused, or completed.

**Relationships:** 

**Business Value:** Enables analysis of how much money is allocated per campaign, which channels are used, and which campaigns are currently active or finished.

**⚠️ Ambiguity Flags:**
- `channel`: channel here lists media types such as social_media, affiliate, paid_search; the same‑named column in orders lists places of purchase like in_store, marketplace, mobile_app, web – no overlapping values, so they likely represent different concepts.
- `status`: status values observed are active, completed, paused; other tables also have a status column with values like active, inactive, churned, cancelled, refunded, discontinued, out_of_stock. The only common word is 'active', which is a generic term and likely coincidental rather than indicating a shared definition.
- `budget`: budget appears as a numeric value with two decimals (e.g., 9988.94) but the currency or unit is not indicated in the data.

## customers

**Purpose:** This table records basic information about customers. It tracks each customer's email, name, signup date, country, segment classification, and current relationship status.

**Columns:**
- `customer_id`: Unique identifier for the customer.
- `email`: Customer's email address.
- `first_name`: Customer's given (first) name.
- `last_name`: Customer's family (last) name.
- `signup_date`: Date the customer account was created.
- `country`: Country where the customer is located.
- `segment`: Business‑defined group such as new, regular, at_risk, high_value.
- `status`: Current state of the customer's relationship, e.g., active, inactive, churned.

**Relationships:** 

**Business Value:** Supports queries about customer demographics, segment distribution, and churn versus active status across regions.

**⚠️ Ambiguity Flags:**
- `status`: status values seen are active, churned, inactive; other tables use status with different sets; only 'active' overlaps, considered a generic term and likely unrelated.
- `segment`: segment categories (new, regular, at_risk, high_value) are not defined in the data, so their exact business meaning is unclear.

## orders

**Purpose:** This table records individual purchase orders placed by customers. It tracks the order date, sales channel, current processing status, and total monetary amount.

**Columns:**
- `order_id`: Unique identifier for the order.
- `customer_id`: Identifier of the customer who placed the order.
- `order_date`: Timestamp when the order was created.
- `status`: Current processing state of the order, such as cancelled or refunded.
- `channel`: Sales channel where the purchase occurred, e.g., in_store, marketplace, mobile_app, web.
- `total_amount`: Total monetary value of the order, shown with two decimal places.

**Relationships:** customer_id links to customers.customer_id.

**Business Value:** Answers which sales channels generate the most revenue, overall order volume, and how many orders are cancelled or refunded.

**⚠️ Ambiguity Flags:**
- `channel`: channel here lists purchase locations like in_store, marketplace, mobile_app, web; the channel column in marketing_campaigns lists media types such as social_media, affiliate, paid_search – no overlapping values, indicating different meanings.
- `status`: status values observed are cancelled, refunded (and possibly delivered in other rows); other tables also have a status column with values like active, completed, paused, inactive, churned, discontinued, out_of_stock. Only 'active' overlaps across tables, which is a generic term and likely unrelated.
- `total_amount`: total_amount is a numeric value with two decimals but the currency or unit is not specified in the data.

## order_items

**Purpose:** This table records the individual line items that belong to each order. It tracks which product was sold, how many units, and the price per unit at the time of purchase.

**Columns:**
- `order_item_id`: Unique identifier for the line‑item record.
- `order_id`: Identifier of the parent order.
- `product_id`: Identifier of the product that was purchased.
- `quantity`: Number of units of the product in this line item.
- `unit_price`: Price per single unit, shown with two decimal places.

**Relationships:** order_id links to orders.order_id; product_id links to products.product_id.

**Business Value:** Allows calculation of revenue per product and analysis of purchase quantities across orders.

**⚠️ Ambiguity Flags:**
- `unit_price`: unit_price is shown as a numeric amount with two decimals, but the currency or unit is not indicated.

## products

**Purpose:** This table lists the products available for sale. It tracks each product's name, category, listed price, and current availability status.

**Columns:**
- `product_id`: Unique identifier for the product.
- `product_name`: Descriptive name of the product.
- `category`: Broad grouping of the product such as beauty, toys, home_goods, sports.
- `price`: Listed price of the product, shown with two decimal places.
- `status`: Current availability of the product, e.g., active, discontinued, out_of_stock.

**Relationships:** 

**Business Value:** Supports queries about product pricing, category performance, and inventory status.

**⚠️ Ambiguity Flags:**
- `status`: status values observed are active, discontinued, out_of_stock; other tables also have a status column with values like completed, paused, inactive, churned, cancelled, refunded. The only shared term is 'active', which is generic and likely unrelated.
- `price`: price is a numeric amount with two decimals but the currency or unit is not specified in the data.
