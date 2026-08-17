# Journey Feedback Transport Design

## Goal

Improve the wedding trip app so activity locations are visible in Journey, feedback feels like a submission, transportation is prioritized in recommendations, and transport WhatsApp links are available from the trip preparation content.

## Design

Journey activity cards will use the existing `trip_activities.address` field already imported from the `atividade_endereco` spreadsheet column. The frontend activity type will expose `address`, and `DayDetails` will render it with a location icon when present.

Feedback will keep the current persistence model and endpoint. The UI copy changes from save language to send language so travelers understand they are submitting feedback to the team. The backend remains unchanged.

Transportation recommendation ordering will be enforced in the recommendations UI by sorting category filters so `Transportation` appears first after `All`, independent of sheet row order.

Wedding transport WhatsApp links will be added through the existing pre-trip links flow. The seed will add `wa.me/55...` useful links to the travel logistics phase for the transport providers already present in Local Recommendations. Reimporting the seed will write those links to the Google Sheet and Supabase.

## Validation

Frontend tests will assert address rendering, send-feedback copy, and Transportation filter order. Backend seed tests will assert transport WhatsApp links are generated in the pre-trip Links tab. After implementation, the wedding content will be reimported and the app/frontend will be redeployed if frontend code changes require it.
