Baseline accuracy check of parse.py v3, 2026-10-17. 35 offer events plus 15 non-offer documents, 90 day window ending 2026-10-15.
Checked by an independent agent reading each press release, not by the parser's author. Tony has not yet verified it.
These rows were seen while building the rules, so any later fix must be tested on a different window.
Kind 49/50, securities 27/35, cap 26/35, expiration 16/35, early date 28/35.

Out of sample test of parse.py v3.2, window of 90 days ending 2026-07-17, checked blind by a separate agent. Rules were frozen before this window was seen.
57 offer events: kind 43/57, securities 45/57, cap 51/57, expiration 49/57 (53/57 if graded on the release text alone), early date 46/57. 15 documents called not an offer: 15/15.
Baseline on the first window for comparison, offer events only: kind 34/35, securities 27/35, cap 26/35, expiration 16/35, early 28/35.
Kind got worse out of sample, which means the first window flattered it. Main kind errors: registered exchange offers and consent only releases called offers, and pricing or final results called launches.
Window B is now used up for tuning. Any new fix needs a window C.

Out of sample test of parse.py v3.3, window of 90 days ending 2026-04-20, never seen before the rules were frozen. Checked blind by a separate agent.
47 offer events: kind 43/47, securities 40/47, cap 38/47, expiration 46/47, early date 45/47. 15 documents called not an offer: 15/15.
Across the three windows on offer events: kind 97 percent, 75 percent, 91 percent. Expiration 46, 86, 98 percent. Cap 74, 89, 81 percent. Securities 77, 79, 85 percent. Early date 80, 81, 96 percent.
Window A was used to build the rules, B was used for the second round, C was blind. Only C is a fair number for v3.3.
Remaining errors: cap basis marked principal when the cap is a purchase price, caps missed or stale after an upsize, new notes counted as targets, zero coupon and CAS style securities with no coupon.
