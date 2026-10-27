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

Out of sample test of parse.py v3.4, window of 90 days ending 2026-01-21, never seen before the rules were frozen. Checked blind by a separate agent.
56 offer events: kind 50/56, securities 38/56, cap 39/56, expiration 49/56, early date 53/56. 15 documents called not an offer: 15/15.
Blind windows C and D combined, 103 offer events: kind 90 percent, securities 76 percent, cap 75 percent, expiration 92 percent, early date 95 percent.
Each new window exposed new failure modes in securities and caps, so regex rules are not converging on those two fields. They stay labeled unverified.
Window D failures: cap basis principal versus purchase price, pool and series caps, upsizes stated in an amendment, targets written as convertible notes or debentures, redeemed notes counted as targets, extended expirations.

Window E, 90 days ending 2025-10-23, never seen before. Head to head test of regex extraction against model extraction on the same 105 documents, graded blind by two separate agents who did not know which extractor was which.
Model extraction was done by Claude agents reading each release with the field definitions in the prompt. The regex side is parse.py v3.4 unchanged.
Regex: is offer 86 percent, kind 97, securities 86, cap 89, expiration 89, early date 92.
Model: is offer 98 percent, kind 100, securities 100, cap 99, expiration 99, early date 100.
Among 87 true offers in the candidate set the regex found 73 and the model found 87. Regex missed Omnicom and Interpublic, Comcast pools, NCL, Fossil, Lazard, Greenidge and Getty releases.
Caveats: the model and the graders are the same family of model, so shared blind spots are possible. Candidate set was the search results, so recall of the search itself is still unmeasured. A human spot check by Tony is still needed.
verify.py checks that securities, caps and dates a model returns appear in the source text. On window E it flagged 8 of 89 model rows, mostly coupon formatting. It did not catch the 2 graded errors, which were wrong attribution rather than invented values.

v3.5 offline fixes, Oct 26 2026. Run on the cached Oct 2026 window only, so these are NOT blind tested and no accuracy number is claimed for them.
Fixes: a redemption sentence with a decimal amount like $1.0 billion no longer lets the redeemed notes count as targets (Open Text 6.900% 2027, Oneok 4.250% 2027). Notes listed as "$1,000 in aggregate principal amount of" in an exchange table are consideration, not targets (two Skydance new notes). Private exchange offers are no longer called registered exchanges (Corteva final results). A result or amendment now joins the offer whose securities it overlaps most, so two offers by one company stay apart (Sabre) and a result no longer inherits another offer's cap. A subsidiary release joins its parent's offer when the securities match (Vylor joins Corteva).
Effect on the 17 current offers: 16 offers after merging, Corteva now shows its full lifecycle and closes, Sabre is two clean offers.
Still open: 10 offers show past expiration with no result filing seen, so the search misses result releases. A follow up search by issuer after expiration is the fix, not written yet because it cannot be tested without the SEC.
