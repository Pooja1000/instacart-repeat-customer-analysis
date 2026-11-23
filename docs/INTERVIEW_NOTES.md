# Interview Notes

Prepared explanations for each methodological choice. No results numbers —
those are in `docs/memo.md` and `results/results.json`.

---

## 1. Leakage Prevention (Observation Window)

**Explanation:** We split each user's history into two non-overlapping windows.
Features come only from orders 1–3 (the "observation window"), and outcomes
come only from orders 4 onward. This strict temporal split ensures we never use
future behaviour to explain future behaviour. If we allowed features and
outcomes to overlap — for example, if basket size was averaged over all orders
including the later ones — the model would partly be predicting itself, leading
to inflated effect sizes and misleading conclusions.

**Likely interview question:** *"How did you ensure there was no data leakage
in your feature engineering?"*

---

## 2. Survivorship Bias

**Explanation:** Every user in this dataset placed at least 4 orders. Customers
who placed fewer than 4 orders are completely absent. This means
our analysis only describes differences among already-retained customers — we
cannot say anything about what makes a first-time buyer come back at all. The
associations we find (e.g., bigger first baskets are associated with becoming a
heavy user) might look different if we could also see the users who placed
fewer than 4 orders, because those users might also have had large first baskets but dropped
off for reasons invisible to us.

**Likely interview question:** *"Your data only has users with 4+ orders. How
does that affect your conclusions?"*

---

## 3. Bootstrap Confidence Intervals

**Explanation:** We use the bootstrap to estimate confidence intervals for group
means without assuming a specific distribution (like normality). We resample
the data with replacement 10,000 times, compute the statistic each time, and
take the 2.5th and 97.5th percentiles of the resulting distribution as the 95%
CI bounds. This is especially useful here because many of our features (like
reorder rate and department shares) have skewed distributions where the normal
approximation would be unreliable. We use a fixed random seed so that every run
produces the same intervals.

**Likely interview question:** *"Why did you use bootstrap CIs instead of
analytical confidence intervals?"*

---

## 4. Logistic Regression and Odds Ratios

**Explanation:** We fit a logistic regression to see which early features are
associated with heavy-user status when considered together — not just one at a
time. Features are standardised (z-scored) so the coefficients and odds ratios
are comparable across features with different scales. An odds ratio of 1.5 on a
standardised feature means that a one-standard-deviation increase in that
feature is associated with 1.5× the odds of being a heavy user, holding other
features constant. We report this as a descriptive tool — not as a prediction
model — and present cross-validated AUC only to gauge how much early behaviour
explains, not as model performance.

**Likely interview question:** *"Why logistic regression instead of a more
complex model? How do you interpret the odds ratios?"*

---

## 5. Two Models: With and Without Gap Features

**Explanation:** We run the regression twice — once excluding the inter-order
gap features (days to second and third order) and once including them. We lead
with the without-gaps version because early gaps partly restate the outcome:
users who come back quickly early on mechanically tend to accumulate more
orders. Including them risks over-attributing the association to timing alone
and suppressing the role of basket composition features. The with-gaps version
is shown for transparency and to illustrate how much timing adds to the
explanation.

**Likely interview question:** *"Why did you run two versions of the model?"*

---

## 6. Sensitivity Analysis

**Explanation:** We defined "heavy user" as the top 25% of users by total order
count (20+ orders). But this threshold is a choice. To check whether our
findings are robust to this choice, we re-ran the analysis with the top 20%
(24+ orders) and top 30% (17+ orders). If the same features rank similarly and
point in the same direction across all three thresholds, we can be more
confident that the associations are real patterns, not artifacts of one
particular cutoff.

**Likely interview question:** *"How do you know your findings aren't just an
artifact of the threshold you chose?"*

---

## 7. Why Descriptive, Not Causal

**Explanation:** All our findings are associations — we see that users with
larger first baskets *tend to* end up as heavy users, but we cannot say that
large first baskets *cause* someone to become a heavy user. There could be
confounders we cannot observe: for example, users who already intended to be
regular customers might place larger first orders because they are committed
from the start. Without randomisation (like an A/B test), we cannot separate
the effect of the behaviour from the effect of the unobserved intent. This is
why our nudge proposals are presented as *experiments to test*, not as proven
interventions.

**Likely interview question:** *"Can you say that increasing basket size will
cause more repeat purchases?"*

---

## 8. Effect Size Thresholds & Why Basket Composition Effects Are Small

**Explanation:** With 206,000+ users, almost any difference — no matter how
tiny — will achieve statistical significance ($p < 0.001$). A p-value tells us
whether we would see a difference this large by chance, but it does not tell us
whether the difference matters in practice. We evaluate continuous features using
standard Cohen's d brackets: negligible ($<0.2$), small ($0.2$–$0.5$), medium
($0.5$–$0.8$), and large ($\ge 0.8$). In our analysis, all early basket composition
and breadth features (department mix, average items) fall into the negligible/small
range ($d < 0.20$; odds ratios $1.03$–$1.14$), whereas early return cadence exhibits
a medium-to-large association ($|d| \approx 0.72$–$0.76$; odds ratios $\approx 0.51$–$0.55$).
This proves that basket mix is a modest early signal compared to customer pacing.

**Likely interview question:** *"You have 200K+ users — isn't everything
statistically significant? How do you assess practical business impact?"*

---

## 9. Data Truncation & Censoring (Orders Capped at 100, Gaps Capped at 30)

**Explanation:** The Instacart dataset exhibits two deliberate boundary truncations:
total orders per user is capped at exactly 100, and inter-order gaps (`days_since_prior_order`)
are capped at 30 days (evidenced by a 19.2× spike at 30 vs 29 days). The 100-order cap
truncates the extreme right tail of super-heavy users, meaning heavy-user thresholds
capture customers with $\ge 20$ orders but compress the distinction between moderate
regulars (e.g. 30 orders) and power users (e.g. 150+ true orders). The 30-day cap
censors long customer churn gaps, compressing the slow tail and making slow users
appear faster than they truly were. However, our primary thresholds (top quartile heavy
status at 20 orders, fast cadence at 7 days) sit comfortably below these caps.

**Likely interview question:** *"Did you notice any artificial censoring or
capping in the data, and how did it affect your metrics?"*
