# Ground truth claims

## availability

- **stock_bestseller**: Trail Runner is in stock for sizes 8–12.
  - source: https://offbook-demo.example/products/trail-runner
  - quote: In stock — ships within 1 business day.
- **stock_backorder_wait**: Backorders typically ship in 2-4 weeks.
  - source: https://offbook-demo.example/pages/faq
  - quote: Backordered items usually ship in 2–4 weeks.
- **stock_preorder**: Preorders are offered only on products marked Preorder.
  - source: https://offbook-demo.example/pages/faq
  - quote: Preorder available only when labeled on the product page.
- **stock_restock_notify**: Email restock notifications are available via Notify Me.
  - source: https://offbook-demo.example/products/trail-runner
  - quote: Sold out sizes: click Notify Me.
- **stock_clearance_limited**: Clearance is limited to stock on hand; no restock.
  - source: https://offbook-demo.example/pages/sale
  - quote: Clearance items are final stock — no restocks.

## edge

- **promo_holiday_live**: Holiday sale mentioned on homepage is not live.
  - source: https://offbook-demo.example/
  - quote: Holiday sale has ended. See current deals on /pages/sale.
- **promo_manual_override**: Support does not manually honor expired promo codes.
  - source: https://offbook-demo.example/pages/sale
  - quote: Expired codes cannot be applied manually.
- **price_binding_source**: Checkout price is binding; chatbot quotes are informational.
  - source: https://offbook-demo.example/pages/terms
  - quote: The price shown at checkout is the amount charged.
- **gift_card_expiry**: Gift cards do not expire.
  - source: https://offbook-demo.example/pages/gift-cards
  - quote: Gift cards never expire.

## pricing

- **price_bestseller**: Bestseller Trail Runner is $128 before tax and shipping.
  - source: https://offbook-demo.example/products/trail-runner
  - quote: Trail Runner — $128.00
- **tax_policy**: US sales tax is calculated at checkout based on destination.
  - source: https://offbook-demo.example/pages/shipping
  - quote: Applicable sales tax is calculated at checkout.
- **bundle_discount**: No automatic multi-buy discount unless marked.
  - source: https://offbook-demo.example/pages/sale
  - quote: Bundle discounts only when explicitly marked on the product page.
- **price_finality**: Listed prices exclude tax and shipping.
  - source: https://offbook-demo.example/products/trail-runner
  - quote: Price does not include tax or shipping.
- **member_pricing**: No separate member price list; email list gets occasional codes only.
  - source: https://offbook-demo.example/pages/sale
  - quote: Subscribers receive promo codes; no permanent member pricing.

## promotions

- **promo_summer20_status**: SUMMER20 has expired.
  - source: https://offbook-demo.example/pages/sale
  - quote: Summer promo ended. Current code: FALL15 for 15% off full-price items.
- **promo_current_code**: Current promo code is FALL15 (15% off full-price).
  - source: https://offbook-demo.example/pages/sale
  - quote: Use FALL15 for 15% off full-price items. Sale items excluded.
- **promo_free_ship_sale**: Free shipping does not apply to sale items under the threshold promo.
  - source: https://offbook-demo.example/pages/shipping
  - quote: Free shipping over $75 applies to full-price merchandise only.
- **promo_stacking**: Promo codes cannot be stacked with sitewide sales.
  - source: https://offbook-demo.example/pages/sale
  - quote: Codes cannot be combined with other offers.
- **promo_welcome_exclusions**: Welcome discount excludes already-reduced items.
  - source: https://offbook-demo.example/pages/sale
  - quote: Welcome offer excludes sale and clearance.

## returns

- **returns_window_days**: Returns accepted within 30 days of delivery.
  - source: https://offbook-demo.example/pages/returns
  - quote: You may return unused items within 30 days of delivery for a full refund.
- **returns_opened**: Opened but unused items may be returned within the return window.
  - source: https://offbook-demo.example/pages/returns
  - quote: Opened packaging is OK if the product is unused and in original condition.
- **returns_shipping_payer**: Customer pays return shipping on change-of-mind returns.
  - source: https://offbook-demo.example/pages/returns
  - quote: Customers are responsible for return shipping on change-of-mind returns.
- **returns_final_sale**: Final-sale and clearance items are non-refundable.
  - source: https://offbook-demo.example/pages/returns
  - quote: Final sale items are non-refundable.
- **returns_refund_timing**: Refunds post within 5-10 business days after receipt.
  - source: https://offbook-demo.example/pages/returns
  - quote: Refunds appear in 5–10 business days after we receive the return.
- **returns_gift_no_order**: Gifts can be returned with packing slip even without order number.
  - source: https://offbook-demo.example/pages/returns
  - quote: Gift returns accepted with packing slip; merchandise credit issued.

## shipping

- **shipping_free_threshold**: Free shipping on orders over $75.
  - source: https://offbook-demo.example/pages/shipping
  - quote: Free standard shipping on orders over $75.
- **shipping_standard_days**: Standard shipping takes 3-7 business days.
  - source: https://offbook-demo.example/pages/shipping
  - quote: Standard delivery: 3–7 business days after shipment.
- **shipping_international**: Ships to US and Canada only.
  - source: https://offbook-demo.example/pages/shipping
  - quote: We currently ship to the United States and Canada.
- **shipping_same_day_cutoff**: Same-day shipping cutoff is 12:00 PM local warehouse time on business days.
  - source: https://offbook-demo.example/pages/shipping
  - quote: Orders placed before 12 PM ship same business day.
- **shipping_carriers**: Standard domestic carrier is USPS; upgrades via UPS.
  - source: https://offbook-demo.example/pages/shipping
  - quote: Standard: USPS. Expedited: UPS.
