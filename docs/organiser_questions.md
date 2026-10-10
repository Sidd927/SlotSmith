# Draft message to organisers / Emerson mentors (not sent)

Post in the Verzii "VIT Code_Apex 3.0" community or send via the official AISF channels. **Do not send without team review.**

---

Hello, we are Team Mac_Enthu (Track 1 · PS 1.2 IO Signal Sudoku). The problem statement mentions a sample IO MDB and an IO allocation template "provided for hackathon use". We could only find the PS PDFs, the handbook and the PPT template on Unstop. Could you please share:

1. The sample IO MDB and the IO allocation template (or tell us when they will be released)?
2. Can a 12-, 6- or 2-pair cable straddle two baseplates, or must every cable of ≤ 12 pairs fit within one baseplate? Must a 24-pair cable start at slot 1 and stay within one CIOC?
3. Spare capacity: is "~10% per cabinet" counted as empty baseplates out of 32, and how is it rounded (e.g. 3.2 → 4)?
4. Should A/B segregation ever apply at cabinet level, or always at CIOC level?
5. How are CIOCs assigned to controllers (one controller per CIOC? a maximum number of CIOCs per controller?), and where do Area/Unit in the naming patterns come from?
6. On a revision, does a CHARM or terminal-block swap in the same slot count as a "move"?

Thank you!

---

## Brief description for the registration form (draft for the team leader)

> SlotSmith automates DeltaV Electronic Marshalling I/O allocation for IO Signal Sudoku. It reads customer IO MDBs, auto-maps columns and raises traceable TQs for bad data. It then places every cable as a block into cabinet → CIOC → baseplate → CHARM slots, following user-editable rules (grouping, A/B segregation, capacity, cable order, spare %, CHARM/terminal block, naming). An independent verifier re-checks every rule on the exported Excel. On Rev B it keeps unchanged signals in place and uses OR-Tools CP-SAT to move as few signals as possible. AI is used only for assistive tasks (column mapping, rule drafting); placement stays deterministic and provable.
