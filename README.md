<img width="563" height="792" alt="Screenshot 2026-11-08 at 4 17 57 PM" src="https://github.com/user-attachments/assets/f3dd2111-b85c-46b4-abde-d67fbf90add8" />
<img width="568" height="735" alt="Screenshot 2026-11-08 at 4 17 33 PM" src="https://github.com/user-attachments/assets/a1f86f7e-cc91-4d43-8085-d71a9f2218e5" />
# Price Scout AI

An AI teammate that researches a product and compares offers for you.
Type a product name and watch it investigate retailers, verify sources, score comparable products and explain its recommendation.

## What it shows

- Retailer price comparison with the best price highlighted
- Source verification (direct listing / third-party report / unverified)
- AI value score for comparable products
- A ribbon (Sankey) chart: brand → product → segment → value
- A plain-language buying recommendation, with an optional spoken briefing

> Prices are AI-reported research. Always confirm the final price with the retailer before buying.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your own OPENAI_API_KEY
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Configuration

| Variable | Required | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | yes | Product research |
| `ELEVENLABS_API_KEY` | no | Spoken briefing |
| `ELEVENLABS_VOICE_ID` | no | Voice for the briefing |

Your `.env` is git-ignored. Never commit real keys.

## Tests

```bash
python -m unittest
```

## Make it yours

The theme lives at the end of `static/style.css` (CSS variables at the top of the "Atlas theme" block), and chart colors are in `static/app.js`.
Fork it and hand your own AI helper a different kind of research job.

## License

MIT
