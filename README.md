# Fragments Made Whole

**Live site: https://ruminate18.github.io/fragments-made-whole/**

Nine broken works from the Harvard Art Museums, each "restored" twice by the same AI image model: once with a generic prompt that knows nothing, and once with a prompt built only from the museum's evidence. The site sets the fragment beside both reconstructions and reads each one against the record: what the evidence supports, and what the machine invented.

## Background

Most objects in an ancient or medieval gallery are pieces of something larger: a head without its statue, a band without its tunic, a painting cut out of its book. How much of the missing whole to show is one of the oldest arguments in conservation.

- The **Venice Charter** (1964), still the reference text for conservators, says restoration "must stop at the point where conjecture begins" (Article 9).
- **Cesare Brandi's** *Theory of Restoration* (1963) asks that any added work be recognizable as new on close inspection, so a repair is never mistaken for the original.
- The 2012 **Ecce Homo** repainting in Borja, Spain, shows what happens when a confident hand fills a gap with invention.
- The **polychromy** debate, made popular by Vinzenz Brinkmann's *Gods in Color* reconstructions, shows how loss itself shapes taste: ancient sculpture and relief were painted, but centuries of bare marble taught viewers to expect white stone.

Generative image models now make reconstructions instantly, seamlessly and with no visible line between what survives and what was imagined. This project tests what they assume, and whether giving them the evidence makes them more faithful or only more convincing.

## The nine cases

Each object was chosen for a different kind of loss.

| # | Object (Harvard Art Museums) | Loss |
|---|---|---|
| 1 | Relief from the tomb of Niankhnesut, Saqqara, Egypt, Dynasty 6 (1934.17) | Lost color; tomb dispersed to 15+ museums |
| 2 | Head of a winged protective spirit, Northwest Palace of Ashurnasirpal II, Nimrud, 883–859 BCE (1940.13) | Lost body |
| 3 | Ahuramazda in the winged disk, Persepolis, 486–460 BCE (1943.1062) | Lost color; sides trimmed for collectors |
| 4 | Wall painting fragment from the villa at Boscotrecase, 10–1 BCE (1921.37) | Lost room |
| 5 | Acrolithic head from a Roman cult statue of a goddess, late 2nd century CE (1905.6) | Lost body (once wood and drapery) |
| 6 | Clavus (tunic band) with Dionysos, Egypt, 400–500 CE (1919.52) | Lost garment; its twin is on a tunic in Boston |
| 7 | Mosaic maenad from the Constantinian Villa, Antioch, 325–350 CE (1939.147) | Lost floor |
| 8 | Bathing Maidens, folio from Nizami's *Haft Paykar*, Iran, c. 1410 (2011.539) | Lost page |
| 9 | Egyptian blue on mud plaster, Palace of Sargon II, Khorsabad (1942.219.1) | Almost everything; the limit case |

## How it works

```
Harvard Art Museums API ──► data/records.json        (object records, provenance, commentary)
IIIF image server       ──► docs/img/fragments/       (museum photographs)
cases.json                                            (evidence + evidence-led prompt per object)
        │
        ▼
generate.py ──► Prodia proxy (Gemini 3 Pro, image-to-image) ──► docs/img/gen/<id>-uninformed.jpg
                                                              docs/img/gen/<id>-evidence.jpg
        │                                                     costs.json (every charge)
        ▼
analysis.json  (reading of each result against the record, written after looking at every image)
        │
        ▼
build_site.py + template.html ──► docs/index.html  ──► GitHub Pages
```

1. **Records.** Object data comes from the [Harvard Art Museums API](https://github.com/harvardartmuseums/api-docs): titles, dates, descriptions, curatorial commentary and provenance. The evidence for each case in `cases.json` is taken from these records.
2. **Two prompts per object.**
   - *Uninformed:* the same sentence for every object, "Restore this damaged artwork to show how it originally looked when it was complete and new."
   - *Evidence-led:* written from the record. It says what survives and must be kept, what is known about the missing parts (the pigment traces at Persepolis, the throne-room position of the Nimrud slab, the twin band in Boston), and what not to invent.
3. **Generation.** `generate.py` sends each museum photograph, resized to fit 1024 × 1024, with each prompt to Gemini 3 Pro (`inference.gemini-3-pro.img2img.v1`) through the course's Prodia proxy. Same model, same input, one call per image. Every result is shown; none were regenerated or chosen for looks. The pipeline was tested first with one FLUX.2 Klein draft ($0.004).
4. **Reading.** Each pair of results was compared against the record and written up in `analysis.json`: what the uninformed guess assumed, what the evidence supports, what the model invented, and a verdict.
5. **Site.** `build_site.py` fills `template.html` and writes a static `docs/index.html`. Nothing runs on a server, so the site is hosted on GitHub Pages.

## Findings

1. **With no evidence, the model mostly cleans.** In six of nine cases the uninformed prompt produced a tidied version of the fragment (sharper carving, filled cracks, rewoven threads) rather than the missing whole. 'Restore' meant 'make it look new', not 'show what is lost'.
2. **It assumes bare stone.** Asked to restore with no evidence, it painted none of the four stone pieces, though the museum records paint on three of them. Given the evidence, it painted all four. The white-marble bias that reconstructions like *Gods in Color* argue against is the model's default.
3. **It can't tell the artwork from the museum.** It restored a modern picture frame, kept a 1935 shipping crate in both versions of the mosaic, and gilded a background that was never gold. Everything in the photograph counts as the object.
4. **Evidence fixes what you ask about and nothing else.** The evidence-led images got the asked-for things right: pigment colors, the inscription band, the acrolith's materials, the page layout. Unasked details moved without warning. The genie lost his horns and turned around, the cow grew horns, a hieroglyphic caption changed, and Persian verse turned into the poet's name repeated.
5. **The prompt is a reconstruction too.** The goddess is seated because my prompt said so, not because anything shows it. Evidence-led prompting doesn't remove conjecture; it moves it from the model to the person writing the prompt, who now carries the conservator's responsibility to mark it.
6. **The best image is the least impressive one.** For the Khorsabad plaster, the uninformed model invented a scarab and the evidence-led model painted a nearly blank wall. Brandi and the Venice Charter would choose the blank wall. A generative model has to be told to stop where conjecture begins, and even then it does not show you where that was.

## Run it yourself

Needs Python 3.9+ with `requests` and `Pillow`, and a key for the course Prodia proxy.

```bash
pip install requests Pillow
cp .env.example .env          # then put your key in .env as PRODIA_PROXY_KEY='...'
python3 generate.py --draft 291721   # one cheap FLUX.2 Klein test
python3 generate.py                  # all final images (skips any already made)
python3 build_site.py                # writes docs/index.html
```

The key is read from `PRODIA_PROXY_KEY` (environment or `.env`), never printed, and `.env` is git-ignored.

## Repository

| Path | What it is |
|---|---|
| `docs/` | The deployed site (published by GitHub Pages) |
| `cases.json` | The nine cases: evidence and evidence-led prompt |
| `analysis.json` | Reading of every result, and the cross-case findings |
| `generate.py` | Calls the Prodia proxy, saves images, logs cost |
| `build_site.py`, `template.html` | Static site generator |
| `data/records.json` | Harvard Art Museums API records for the nine objects |
| `costs.json` | Every Prodia charge for this project |

## Cost

18 Gemini 3 Pro images at $0.15 each, plus 1 FLUX.2 Klein test draft ($0.004): **$2.70** of the course's $10 Prodia budget. Every charge is logged in `costs.json`.

## Limits

- One generation per prompt. Image models vary from run to run, so a single image is one sample of what the model does, not its only answer.
- The evidence-led prompts are only as good as their sources: museum records and general art-historical knowledge, not new research on each object.
- The reconstructions are speculative images, not evidence, and should not be reused as depictions of the originals.

## Credits

- Object data and images: Harvard Art Museums. Images © President and Fellows of Harvard College, used for study.
- Image generation: Gemini 3 Pro via Prodia, through the course proxy.
- Built with help from Claude (Anthropic) as a coding and research assistant.
