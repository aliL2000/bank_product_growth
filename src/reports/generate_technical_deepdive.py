"""Generate reports/Technical_Deep_Dive.pdf - the technical companion to
Project_Recap.pdf. Where the recap explains *what* was built for a
non-technical reader, this explains *why* each method was chosen, what the
alternatives were, and links to primary documentation for each concept.

Content mirrors docs/concepts_log.md plus the reasoning behind each decision
in docs/decisions/ and ROADMAP.md. Rerun this script after a session that
introduces new techniques worth documenting at this depth.

Usage: python src/reports/generate_technical_deepdive.py
"""

from pathlib import Path

from fpdf import FPDF

OUT_PATH = Path(__file__).resolve().parents[2] / "reports" / "Technical_Deep_Dive.pdf"

TEAL = (16, 94, 107)
DARK = (30, 41, 59)
GRAY = (100, 110, 120)
BOX_BG = (237, 242, 245)
BOX_BORDER = (16, 94, 107)
LINK_BLUE = (30, 90, 200)
LINK_BOX_BG = (232, 240, 250)
AMBER = (156, 92, 8)
AMBER_BG = (252, 241, 224)
AMBER_BORDER = (200, 130, 20)


class DeepDive(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def part_title(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 17)
        self.set_text_color(*DARK)
        self.cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
        y = self.get_y()
        self.set_draw_color(*TEAL)
        self.set_line_width(1.0)
        self.line(self.l_margin, y, self.l_margin + self.epw, y)
        self.ln(5)

    def topic_title(self, number, text, planned=False):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*TEAL)
        label = f"{number}. {text}"
        self.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
        if planned:
            self.set_font("Helvetica", "BI", 8.5)
            self.set_text_color(*AMBER)
            self.cell(0, 5, "PLANNED - decided, not yet implemented", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def label_body(self, label, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*DARK)
        self.cell(0, 5.5, label, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.3, text, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def learn_more(self, links):
        """links: list of (title, url) tuples, rendered as clickable text."""
        pad = 2.5
        self.set_font("Helvetica", "B", 9.5)
        line_h = 5.2
        title_h = line_h + pad * 2
        link_h = line_h * len(links)
        box_h = title_h + link_h
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*LINK_BOX_BG)
        self.set_draw_color(*LINK_BLUE)
        self.set_line_width(0.5)
        self.rect(x, y, self.epw, box_h, style="DF")
        self.set_xy(x + pad, y + pad)
        self.set_text_color(*DARK)
        self.cell(0, line_h, "Learn more:", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "U", 9.5)
        self.set_text_color(*LINK_BLUE)
        for title, url in links:
            self.set_x(x + pad * 2)
            self.cell(0, line_h, title, link=url, new_x="LMARGIN", new_y="NEXT")
        self.set_xy(x, y + box_h + 4)

    def planned_banner(self, text):
        pad = 3
        self.set_font("Helvetica", "B", 10)
        lines = self.multi_cell(self.epw - 2 * pad, 5.2, text, dry_run=True, output="LINES")
        box_h = pad * 2 + 5.2 * len(lines)
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*AMBER_BG)
        self.set_draw_color(*AMBER_BORDER)
        self.set_line_width(0.8)
        self.rect(x, y, self.epw, box_h, style="DF")
        self.set_xy(x + pad, y + pad)
        self.set_text_color(*AMBER)
        self.multi_cell(self.epw - 2 * pad, 5.2, text, align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_xy(x, y + box_h + 4)


def topic_block(pdf, number, title, why, how, alt, watch, links, planned=False):
    pdf.topic_title(number, title, planned=planned)
    pdf.label_body("Why here:", why)
    pdf.label_body("How it works:", how)
    pdf.label_body("Alternatives considered:", alt)
    pdf.label_body("Watch out for:", watch)
    if links:
        pdf.learn_more(links)
    pdf.ln(2)


def build():
    pdf = DeepDive(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(20, 18, 20)

    # --- Cover / intro ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 21)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 11, "Technical Deep-Dive: Methodology & Concepts", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(
        0, 6,
        "The technical companion to Project_Recap.pdf: why each method was "
        "chosen, what the alternatives were, and where to learn more.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.multi_cell(
        0, 5,
        "Prepared September 2026 - covers the reasoning behind Phase 0 and "
        "Phase 1 work, all of Phase 2's data engineering (split, feature "
        "engineering, a self-audit fix) and its first trained model "
        "(logistic regression), plus the decided (not yet implemented) "
        "plan for the rest of Phase 2.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(
        0, 5.6,
        "Project_Recap.pdf explains what was built, for a reader with no ML "
        "background. This document is the other half: for each non-trivial "
        "technique used so far, it lays out why that technique was the right "
        "tool for this specific problem, what else was considered and why it "
        "wasn't picked, common pitfalls, and a link to primary documentation "
        "if you want to go deeper.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(1.5)
    pdf.multi_cell(
        0, 5.6,
        "Sections are grouped by project phase. Part 1 through Part 5 cover "
        "work that is done and verified against real output - Part 4 "
        "covers Phase 2's data engineering (the three-way split, feature "
        "engineering, and a self-audit that caught a real bug), and Part 5 "
        "covers Phase 2's first trained model. Part 6 covers what's still "
        "planned for the rest of Phase 2 - genuinely decided, with reasons, "
        "but not yet written as code - and is marked accordingly.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)
    pdf.planned_banner(
        "A note on how to read this: every section follows the same four "
        "questions - why this was needed here, how it actually works, what "
        "the alternatives were, and what commonly goes wrong with it. That "
        "structure is deliberate: the goal is for you to be able to reuse "
        "this reasoning on a similar problem, not just this project."
    )

    # ================= PART 1 =================
    pdf.add_page()
    pdf.part_title("Part 1 - Data Engineering Foundations")

    topic_block(
        pdf, 1, "Out-of-core (chunked) CSV reading",
        why=(
            "train_ver2.csv is 2.29 GB on disk with 13.6M rows and 48 columns. "
            "Extrapolating from a 100k-row sample, loading every column at "
            "once would land around 15 GB in memory - close enough to this "
            "machine's headroom to risk swapping or a crash, just to compute "
            "row counts and missing-value counts."
        ),
        how=(
            "pd.read_csv(path, chunksize=500_000) returns an iterator instead "
            "of a DataFrame. Each iteration parses only the next 500k rows; "
            "you accumulate whatever summary statistic you need (counts, "
            "sums) across chunks, and the previous chunk becomes eligible for "
            "garbage collection once you're done with it. Peak memory is "
            "bounded by one chunk's size, not the whole file."
        ),
        alt=(
            "Dask or Polars (out-of-core / parallel dataframe libraries) "
            "could handle this more natively and would scale further, but "
            "add a new dependency and API surface for a project whose goal "
            "is demonstrating the standard pandas/scikit-learn workflow. "
            "Chunking with vanilla pandas was simpler and fully sufficient "
            "given the computations needed (running counts) fit the "
            "accumulator pattern below."
        ),
        watch=(
            "Chunking only helps for computations expressible as a running "
            "accumulation (sums, counts, min/max). Anything needing the whole "
            "dataset at once - a global sort, a join across rows that might "
            "land in different chunks - needs a different algorithm. Chunk "
            "boundaries are arbitrary row cuts, not aligned to any logical "
            "grouping, so a single customer's monthly rows can land in "
            "different chunks - this is why the adoption-label join (Topic "
            "3) needed a different approach entirely, not just bigger chunks."
        ),
        links=[("pandas - Scaling to large datasets", "https://pandas.pydata.org/docs/user_guide/scale.html")],
    )

    topic_block(
        pdf, 2, "Column pruning + dtype downcasting (including categorical dtype)",
        why=(
            "The adoption-label build only needs 3 of 48 columns; the EDA's "
            "profile join needs 9. Narrowing both which columns are loaded "
            "and their dtypes (int64 -> int32/int8, free-text strings -> "
            "category) cut memory from a hypothetical ~15 GB down to a few "
            "hundred MB each time, avoiding the chunking machinery entirely "
            "for these steps."
        ),
        how=(
            "usecols= and an explicit dtype= dict are applied at parse time, "
            "so pandas never allocates the wider representation in the first "
            "place. The category dtype specifically stores a small integer "
            "code per row plus a lookup table of unique values, instead of "
            "repeating the full string on every row - this matters a lot for "
            "low-cardinality columns like segmento or canal_entrada."
        ),
        alt=(
            "Loading everything with default dtypes and calling .astype() "
            "afterward - rejected because it still pays the peak-memory cost "
            "of the wide, naive load before you get the chance to shrink it, "
            "defeating the purpose."
        ),
        watch=(
            "Picking a dtype too narrow (e.g. int8 for a column that turns "
            "out to exceed 127) raises a LossySetitemError or silently wraps "
            "depending on the operation - check the real min/max first, "
            "don't guess. Categorical dtype's benefit shrinks (and can even "
            "add overhead) for genuinely high-cardinality columns, where the "
            "lookup table itself becomes large."
        ),
        links=[
            ("pandas - Scaling to large datasets (dtypes section)", "https://pandas.pydata.org/docs/user_guide/scale.html"),
            ("pandas - Categorical data", "https://pandas.pydata.org/docs/user_guide/categorical.html"),
        ],
    )

    topic_block(
        pdf, 3, "Merge-based lag join for panel (longitudinal) data",
        why=(
            "The adoption label needs, for every (customer, month) row, "
            "whether that same customer held a credit card in the "
            "immediately preceding calendar month. 7.1% of rows have no "
            "record from exactly one month before (new customers, or gaps "
            "where a customer temporarily left the bank's radar)."
        ),
        how=(
            "A lookup table keyed on (ncodpers, month) is built, then each "
            "row is merged against that lookup at (ncodpers, month - 1) "
            "using pandas Period arithmetic, so month-length issues are "
            "handled correctly. Rows with no match get an explicitly-defined "
            "'unknown' label rather than a guessed value."
        ),
        alt=(
            "groupby('ncodpers')[flag].shift(1) is the standard idiom for "
            "this and is fine when a panel has no gaps - it shifts by row "
            "position within the group, not by elapsed time. Rejected here "
            "specifically because of the 7.1% gap rate: a positional shift "
            "would silently compare, say, March to January and call it "
            "'last month,' producing a wrong label with no error."
        ),
        watch=(
            "It's tempting to treat 'no prior row' the same as 'didn't have "
            "the product' (impute 0) - that inflates the adoption-event "
            "count with cases that are actually 'customer just joined and "
            "immediately had it,' not genuine adoption. Here, 964,888 rows "
            "(7.1%) were explicitly excluded from the eligible population "
            "instead."
        ),
        links=[
            ("pandas - Merge, join, concatenate and compare", "https://pandas.pydata.org/docs/user_guide/merging.html"),
            ("Wikipedia - Panel data", "https://en.wikipedia.org/wiki/Panel_data"),
        ],
    )

    # ================= PART 2 =================
    pdf.add_page()
    pdf.part_title("Part 2 - Framing the Prediction Problem")

    topic_block(
        pdf, 4, "Choosing the target product via a prevalence-based framework",
        why=(
            "24 candidate products existed. The target needed to (a) have "
            "enough of both classes to actually learn from, (b) be something "
            "the bank's marketing can plausibly influence, so a targeting "
            "recommendation in Phase 4 means something, and (c) carry enough "
            "correlated signal to be interesting for Phase 3 explainability."
        ),
        how=(
            "Month-by-month prevalence for the three shortlisted candidates "
            "was computed via the chunked-scan technique from Topic 1 across "
            "all 17 months, then combined with qualitative reasoning about "
            "'actionability' - marketing can plausibly cause credit-card "
            "adoption; it can't cause a payroll-account switch, which is "
            "driven mainly by a customer changing employers."
        ),
        alt=(
            "Mutual funds - plausible, never numerically ruled out, just "
            "judged likely narrower and more wealth-segment-concentrated "
            "without spending time confirming, since credit card's case was "
            "strong enough on its own. Payroll account - ruled out "
            "specifically on the 'can the bank actually cause this?' test."
        ),
        watch=(
            "Prevalence alone isn't sufficient. A target can have plenty of "
            "both classes and still be a bad choice if the business action "
            "downstream (marketing outreach) can't plausibly move the "
            "needle on it - that's a business-judgment check, not something "
            "a metric alone will catch."
        ),
        links=[],
    )

    topic_block(
        pdf, 5, "Rare-event labels and class imbalance",
        why=(
            "0.57% of eligible customer-months resulted in an adoption event "
            "- a heavily imbalanced binary target. A model that always "
            "predicts 'no' is right 99.43% of the time and completely "
            "useless, since it never identifies anyone to target."
        ),
        how=(
            "The label itself isn't 'fixed' at this stage - the imbalance is "
            "real and meaningful. What has to change is how the eventual "
            "model is evaluated and used: accuracy is abandoned as a metric "
            "in favor of a ranking-based one (Topic 6), and Phase 2's model "
            "training will lean on class weighting rather than "
            "misleadingly resampling the data."
        ),
        alt=(
            "Resampling techniques (oversampling the minority class, e.g. "
            "SMOTE, or undersampling the majority) are the other common "
            "answer to imbalance. Current plan leans toward NOT resampling, "
            "and instead using class_weight (supported natively by both "
            "logistic regression and LightGBM) plus rank-based evaluation, "
            "since resampling distorts the true prevalence a business "
            "stakeholder needs to reason about honestly."
        ),
        watch=(
            "If resampling is used at all, it must only touch the training "
            "set - evaluating on a resampled validation set is a "
            "leakage-adjacent mistake, since it no longer reflects the "
            "real-world class balance the model will actually face."
        ),
        links=[
            ("scikit-learn - Precision-Recall example (imbalance context)", "https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html"),
        ],
    )

    topic_block(
        pdf, 6, "Precision@K over accuracy as the success metric",
        why=(
            "The real business action is a ranked list - 'contact the top K "
            "most likely customers' - not a yes/no classification of the "
            "whole customer base. Precision@K directly measures 'of the K "
            "customers actually acted on, how many were real adopters,' "
            "which maps onto the real decision in Phase 4's cost/benefit "
            "framing."
        ),
        how=(
            "Rank all eligible customers by predicted adoption probability; "
            "take the top K (K set by a marketing budget / contact "
            "capacity); compute the fraction of those K that are true "
            "positives."
        ),
        alt=(
            "ROC-AUC - a common default, but summarizes performance across "
            "every possible threshold, most of which the business would "
            "never operate at (nobody is contacting 80% of the customer "
            "base). F1 score - better than accuracy, but still assumes a "
            "single global threshold rather than a ranked top-K cutoff."
        ),
        watch=(
            "Precision@K is threshold/K-dependent by design - always report "
            "it alongside the K it was measured at, ideally at a couple of "
            "different K values, since the 'right' K in practice is a "
            "business budget question, not a modeling one."
        ),
        links=[
            ("scikit-learn - Precision-Recall example", "https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html"),
        ],
    )

    # ================= PART 3 =================
    pdf.add_page()
    pdf.part_title("Part 3 - Exploratory Analysis Methodology")

    topic_block(
        pdf, 7, "Point-in-time correctness (avoiding leakage)",
        why=(
            "Comparing adoption rate by customer segment (age, tenure, "
            "income, activity) required attaching profile attributes to "
            "each labeled row. Using that customer's attributes from the "
            "SAME month as the label risks leakage: an attribute could "
            "itself be a downstream consequence of the event, not a cause "
            "available beforehand."
        ),
        how=(
            "Every labeled row is joined to that customer's profile at "
            "month t-1 (before the adoption could have happened), using the "
            "same merge-key trick as Topic 3. This guarantees every "
            "attribute used was knowable at the point a real targeting "
            "decision would have to be made."
        ),
        alt=(
            "There isn't a real alternative once the risk is understood - "
            "the only 'alternative' is the wrong approach (using month t "
            "attributes), included here as the concrete failure mode this "
            "guards against."
        ),
        watch=(
            "Leakage is usually far subtler in practice than this example. "
            "A common real-world case: computing a global mean or scaling "
            "factor over the entire dataset before a time-based split lets "
            "information from later months quietly influence how earlier "
            "rows are represented. The general test: could this value have "
            "been known at the moment the targeting decision would actually "
            "be made?"
        ),
        links=[
            ("scikit-learn - Common pitfalls (data leakage)", "https://scikit-learn.org/stable/common_pitfalls.html"),
        ],
    )

    topic_block(
        pdf, 8, "Quantile binning vs. fixed-width binning",
        why=(
            "renta (income) is heavily right-skewed with a small number of "
            "extreme high-income outliers (max ~28.9M vs. median ~102k). "
            "Fixed-width bins would dump the vast majority of customers into "
            "one or two buckets and leave the rest nearly empty, making the "
            "segment comparison useless."
        ),
        how=(
            "pd.qcut splits on sample quantiles, so each bucket holds "
            "(approximately) the same number of observations, regardless of "
            "how the underlying values are distributed."
        ),
        alt=(
            "pd.cut (fixed-width bins) was used deliberately for age and "
            "tenure instead, where the ranges are naturally bounded and "
            "evenly meaningful - a '40-50' age bucket is a genuinely "
            "comparable-width life stage in a way an income range isn't, "
            "given the skew."
        ),
        watch=(
            "Quantile bin edges are data-dependent - they shift if rows are "
            "added/removed or the time window changes, so they aren't "
            "stable thresholds you can reuse in production without freezing "
            "them explicitly (e.g. computing them once on a training set "
            "and reusing those exact edges going forward)."
        ),
        links=[("pandas.qcut reference", "https://pandas.pydata.org/docs/reference/api/pandas.qcut.html")],
    )

    # ================= PART 4 =================
    pdf.add_page()
    pdf.part_title("Part 4 - Phase 2: Split, Feature Engineering & Data Quality")

    topic_block(
        pdf, 9, "Time-based (period) train/validation/test split",
        why=(
            "The real use case predicts the future from the past. A random "
            "split would validate the model on rows chronologically mixed "
            "in with training rows, letting validation performance reflect "
            "an unrealistic scenario. A two-way split has a second, subtler "
            "problem once more than one model is being compared: using the "
            "same validation set both to pick the best model and to report "
            "its final performance number is a mild form of double-dipping "
            "that biases the reported number optimistically."
        ),
        how=(
            "src/features/train_val_split.py tags every eligible labeled "
            "row three ways by calendar month, no random component: train "
            "= the earliest 11 months (2015-02 to 2015-12), val = the next "
            "2 months (2016-01/02), test = the final 3 months (2016-03 to "
            "2016-05) - held out and reported on exactly once. Result: "
            "train 7,694,326 rows / 48,696 adoptions (0.633%), val "
            "1,751,740 / 7,673 (0.438%), test 2,665,623 / 12,749 (0.478%)."
        ),
        alt=(
            "Time-series cross-validation (rolling-origin, multiple folds) "
            "is the more rigorous version of the same idea; a single fixed "
            "three-way cutoff was used instead since the immediate priority "
            "is a stable set of boundaries to compare a couple of models "
            "against, not a full CV study. A simpler two-way split with a "
            "documented optimism caveat was also considered and rejected - "
            "the three-way split removes the caveat entirely rather than "
            "just disclosing it."
        ),
        watch=(
            "The test set only does its job if it's genuinely left alone "
            "until the very end - looking at test performance to inform an "
            "earlier decision (which features to keep, which "
            "hyperparameters to try) quietly turns it into a second "
            "validation set and undoes the whole point. Full reasoning in "
            "docs/decisions/004-three-way-split.md."
        ),
        links=[
            ("scikit-learn - TimeSeriesSplit", "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html"),
        ],
    )

    topic_block(
        pdf, 10, "Train-fit imputation with a missingness indicator flag",
        why=(
            "The first Phase 2 feature group (tenure via antiguedad, and "
            "activity via ind_actividad_cliente) has a small share of "
            "missing values (0.161% of rows, after also converting "
            "antiguedad's -999999 bad-data placeholder to a proper NaN). "
            "Those need a fill value - and computing it from train+val "
            "combined would let val rows quietly influence the value used "
            "to fill train rows, a smaller instance of the same leakage "
            "Topic 9 guards against structurally."
        ),
        how=(
            "src/features/build_features_tenure_activity.py computes the "
            "fill value (median for tenure, mode for activity) using only "
            "rows tagged 'train', then applies that single fixed value to "
            "both splits via .fillna(). Before filling, an isna() snapshot "
            "is saved into a separate *_missing boolean column per feature, "
            "so a downstream model can still distinguish 'genuinely had "
            "this value' from 'value was unknown and got the fallback.'"
        ),
        alt=(
            "Dropping rows with missing values - rejected, since even a "
            "small missing rate compounds across many feature groups and "
            "would shrink the usable dataset for no real benefit here. "
            "Fitting the imputer on the full dataset (train+val) before "
            "splitting - the simplest-looking approach, and the one "
            "rejected specifically for the leakage reason described above."
        ),
        watch=(
            "This pattern has to be repeated for every imputed feature "
            "added in later Phase 2 groups (income, channel, etc.) - easy "
            "to forget on a later feature and compute a fill value across "
            "the full dataset out of habit. Also, a train-fit median/mode "
            "can technically fall outside val's true distribution if it has "
            "shifted over time (which the Phase 1 EDA already showed for "
            "tenure/activity) - that's expected and correct, not a bug to "
            "fix by refitting on val."
        ),
        links=[
            ("scikit-learn - Imputation of missing values", "https://scikit-learn.org/stable/modules/impute.html"),
        ],
    )

    topic_block(
        pdf, 11, "Group-wise imputation for a segment-varying, skewed feature",
        why=(
            "renta (income) is about 20% missing, and unlike tenure/"
            "activity, typical income genuinely differs a lot by the "
            "bank's own customer segment (segmento medians ranged ~89k-"
            "142k across segments vs. one global median around 102k) - a "
            "single flat fill value would distort segments differently."
        ),
        how=(
            "build_features_demographics.py computes each segmento's "
            "train-only median income and fills a missing row with its own "
            "segment's median, falling back to the train-only global "
            "median for the ~1.4% of rows where segmento itself is also "
            "missing."
        ),
        alt=(
            "A single global median (Topic 10's approach) - appropriate "
            "there since tenure/activity don't vary much by segment, "
            "rejected here since it would wash out a real, sizeable "
            "difference. A full regression-based imputer (predicting "
            "income from other features) - judged as overkill for a "
            "baseline, given the segmento breakdown already captures most "
            "of the meaningful variation cheaply."
        ),
        watch=(
            "Group-wise imputation needs an explicit fallback for rows "
            "missing the grouping key itself - assuming every row has a "
            "valid group to fall back on is an easy way to end up with "
            "silent NaN propagation instead of a filled value."
        ),
        links=[
            ("scikit-learn - Imputation of missing values", "https://scikit-learn.org/stable/modules/impute.html"),
        ],
    )

    topic_block(
        pdf, 12, "Log-transforming a right-skewed feature",
        why=(
            "renta's raw distribution is heavily right-skewed (mean ~135k "
            "vs. median ~102k, max ~29M). A linear model like logistic "
            "regression is sensitive to a handful of extreme values "
            "dominating its fitted coefficient, and on the raw scale, "
            "typical variation among most customers looks tiny next to a "
            "few extreme incomes."
        ),
        how=(
            "renta_log = log1p(renta_imputed) compresses the right tail "
            "while preserving rank order, making typical-range differences "
            "much more visible to a linear model. log1p (log(1+x) instead "
            "of plain log(x)) avoids an undefined result if any value were "
            "ever exactly 0."
        ),
        alt=(
            "Winsorizing/clipping extreme values, or quantile-binning "
            "income into buckets (Topic 8's technique, useful for EDA "
            "readability) - a continuous log transform was chosen for the "
            "modeling feature instead since it preserves a smooth "
            "relationship rather than discretizing it. Confirmed "
            "empirically: renta_log's correlation with adoption (~0.022) "
            "was 2.6x renta_imputed's (~0.008)."
        ),
        watch=(
            "A log transform only reshapes scale - it can't turn an "
            "unrelated feature into a predictive one. It's also purely for "
            "the linear model's benefit: LightGBM's tree splits are "
            "invariant to any monotonic transform of a feature, so this "
            "step does nothing for it either way."
        ),
        links=[
            ("numpy.log1p reference", "https://numpy.org/doc/stable/reference/generated/numpy.log1p.html"),
        ],
    )

    topic_block(
        pdf, 13, "Catching a contaminated negative class via self-audit",
        why=(
            "A structured self-review (the project's own '/audit' "
            "process) of the split and feature files in place at the time "
            "found that ~4.5% of rows still belonged to customers who "
            "already held a credit card at t-1. For those rows, "
            "'adoption' is trivially False - they can't newly adopt "
            "something they already have - so those rows were quietly "
            "diluting every correlation number computed against that "
            "population, including feature-check notebooks already run."
        ),
        how=(
            "Fixed at the earliest point in the pipeline: "
            "train_val_split.py now filters to label_defined & "
            "(prev_flag == 0) before assigning train/val/test, so every "
            "downstream feature file and notebook automatically inherits "
            "the correction rather than needing individual patches."
        ),
        alt=(
            "Patching each downstream correlation/notebook individually - "
            "rejected, since the wrong population would keep "
            "re-contaminating anything built on top of it later. Fixing "
            "the root population once was safer and cheaper."
        ),
        watch=(
            "The numbers moved after the fix, not just noise - "
            "product_count_prev's correlation rose from ~0.13 to ~0.163 "
            "(the contaminated rows were diluting it, not inflating it). "
            "'Eligible population' is a substantive modeling decision, not "
            "an implementation detail - getting it wrong changes actual "
            "conclusions, not just downstream accuracy. Full reasoning in "
            "docs/decisions/003-eligibility-filter.md."
        ),
        links=[],
    )

    topic_block(
        pdf, 14, "Per-bin lift tables vs. Pearson correlation for a non-monotonic feature",
        why=(
            "age_years's Pearson correlation with adoption came out as a "
            "'weak' 0.0356, despite Phase 1 EDA already visually noticing "
            "adoption peaking in middle age - a sign the yardstick, not "
            "the feature, might be the problem."
        ),
        how=(
            "Pearson correlation measures how well a straight line fits a "
            "relationship; when a pattern rises then falls, positive and "
            "negative deviations partially cancel out in the calculation. "
            "A per-bin lift table (bucket the feature, compute the target "
            "rate per bucket vs. the overall rate) makes no assumption "
            "about shape. Built on train (12 age buckets): lift ranged "
            "from ~0.04x at 20-25 up to ~2.04x at 45-50, back down to "
            "~0.29x at 80+ - a real, roughly 50x range that Pearson badly "
            "understated."
        ),
        alt=(
            "Spearman rank correlation - considered and rejected, since it "
            "only fixes monotonic-but-nonlinear relationships, not a curve "
            "that both rises and falls; it would repeat Pearson's mistake "
            "in a different form."
        ),
        watch=(
            "Confirming the real shape doesn't automatically let a linear "
            "model use it - logistic regression still needed an explicit "
            "age_years_sq term (centered on the train-only mean before "
            "squaring, to keep the two terms less correlated with each "
            "other) to approximate the parabola. LightGBM shares the same "
            "feature set and did make some use of age_years_sq (27 splits), "
            "but far less than age_years alone (292 splits) - trees find "
            "most of the non-monotonic pattern from the raw feature "
            "natively, so the engineered term isn't essential there the "
            "way it is for logistic regression's single linear term."
        ),
        links=[],
    )

    topic_block(
        pdf, 15, "Merge-safety validation and a growing automated test suite",
        why=(
            "This pipeline is built from several sequential joins (label, "
            "three feature groups, final assembly), all keyed on "
            "(ncodpers, fecha_dato). A silent duplicate key on either side "
            "of any merge would fan out rows without raising an error, "
            "corrupting everything downstream with no visible symptom "
            "until much later."
        ),
        how=(
            "Every merge in the pipeline uses pandas' "
            "merge(..., validate='one_to_one'), which raises immediately "
            "on a duplicate key on either side, plus an explicit "
            "assert len(merged) == len(base) right after (validate only "
            "checks keys, not that every row found a match). A pytest "
            "suite (19 tests as of this session) exercises the "
            "label-building logic, each feature script's point-in-time "
            "join, and the final assembly step against small synthetic "
            "frames - runnable directly from VSCode's Test Explorer."
        ),
        alt=(
            "Manually eyeballing row counts after each script run - what "
            "the project did at first, upgraded once the pipeline grew "
            "past a couple of scripts, since a manual check is easy to "
            "skip under time pressure and doesn't run automatically."
        ),
        watch=(
            "validate='one_to_one' only proves a join was safe given the "
            "keys it saw - it can't catch a case where the keys are "
            "unique but wrong (e.g. accidentally joining month t instead "
            "of month t-1). That's a different failure mode, guarded "
            "against separately by each feature script's own "
            "point-in-time logic (Topic 7)."
        ),
        links=[
            ("pandas.DataFrame.merge reference", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html"),
        ],
    )

    # ================= PART 5 =================
    pdf.add_page()
    pdf.part_title("Part 5 - Phase 2: The Baseline Model (implemented)")

    topic_block(
        pdf, 16, "Logistic regression as the baseline",
        why=(
            "Before reaching for a more powerful model, this project needed "
            "a simple, fast, fully interpretable reference point. Its "
            "coefficients are directly readable (a one-standard-deviation "
            "move in a standardized feature shifts the log-odds of "
            "adoption by its coefficient), making it a genuine sanity "
            "check rather than a black box, and it trains in seconds even "
            "at this row count."
        ),
        how=(
            "Models the log-odds of the binary outcome as a linear "
            "combination of the input features; a sigmoid function converts "
            "that linear score into a probability between 0 and 1. Fit on "
            "the 7.69M-row train split using 16 features (renta_log in "
            "place of the collinear renta_imputed), with continuous "
            "features standardized on train-only statistics."
        ),
        alt=(
            "Skipping straight to LightGBM - rejected because without a "
            "simple baseline there's no way to tell how much of the final "
            "model's performance comes from genuine nonlinear pattern-"
            "finding versus how much a dead-simple linear model would have "
            "captured anyway. The gap between the two is itself the "
            "interesting number."
        ),
        watch=(
            "Logistic regression assumes a roughly linear relationship "
            "between each feature and the log-odds of the outcome. Age's "
            "known non-monotonic pattern (Topic 14) was handled directly "
            "rather than left as a caveat: adding age_years_sq let the "
            "model approximate the parabola, and the fitted coefficients "
            "confirmed it worked - activity_index and product_count_prev "
            "came out strongly positive, age_years positive with "
            "age_years_sq negative, tracing the same 45-50 peak. Result: "
            "ROC-AUC 0.906 (train) / 0.912 (val) - no sign of overfitting "
            "- and ~14-17x lift among the top 1% of customers by score."
        ),
        links=[("scikit-learn - Linear Models (logistic regression)", "https://scikit-learn.org/stable/modules/linear_model.html")],
    )

    topic_block(
        pdf, 17, "Class weighting for imbalanced classification",
        why=(
            "With adoption at ~0.6% of rows, an unweighted logistic "
            "regression fit to minimize total error has little incentive "
            "to push predicted probabilities for real adopters above those "
            "for non-adopters - the opposite of what a ranking/targeting "
            "use case needs. This makes concrete the class-imbalance "
            "strategy decided back in Topic 5."
        ),
        how=(
            "sklearn's class_weight='balanced' sets each class's weight to "
            "n_samples / (n_classes * n_samples_in_that_class), so the "
            "rare class (adopters) gets a much larger weight in the loss "
            "function - passed straight into LogisticRegression(...), no "
            "separate resampling step needed."
        ),
        alt=(
            "Oversampling adopters (e.g. SMOTE) or undersampling "
            "non-holders - both change what rows the model actually sees "
            "and can introduce artifacts (duplicated or synthetic rows). "
            "Reweighting keeps every real row exactly as observed, "
            "consistent with the no-resampling stance decided in Topic 5."
        ),
        watch=(
            "Reweighting shifts predicted probabilities away from true "
            "real-world frequencies - a 'balanced' model's 0.5 output "
            "doesn't mean a 50% real-world chance. Fine for ranking "
            "customers by score (this project's actual use case), but a "
            "reason not to read its raw probabilities as calibrated "
            "real-world estimates without further calibration work."
        ),
        links=[
            ("scikit-learn - LogisticRegression class_weight parameter", "https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html"),
        ],
    )

    # ================= PART 6 =================
    pdf.add_page()
    pdf.part_title("Part 6 - Phase 2 Plan: The Stronger Model")
    pdf.planned_banner(
        "Everything in this part is a decided plan with real reasoning "
        "behind it, not yet-written code. Treat it as 'here's the plan and "
        "why,' and expect this section to be revised once it's actually "
        "implemented and tested against real results."
    )

    topic_block(
        pdf, 18, "Gradient-boosted trees (LightGBM) as the stronger model",
        why=(
            "Tabular data with a mix of numeric and categorical features, a "
            "nonlinear relationship for age, and likely interactions "
            "between features (does tenure matter more for active "
            "customers?) - exactly the regime where gradient-boosted "
            "decision trees consistently outperform linear models, and "
            "usually most deep learning approaches too, on tabular data."
        ),
        how=(
            "Builds an ensemble of shallow decision trees sequentially: each "
            "new tree is trained to correct the residual errors of the "
            "trees built so far, and the final prediction is a weighted sum "
            "across all trees. LightGBM's specific contribution is speed - "
            "histogram-based split finding and leaf-wise tree growth - so "
            "it scales well to the ~12M-row eligible population here."
        ),
        alt=(
            "XGBoost or CatBoost - comparable gradient-boosting "
            "implementations, arguably more common in production settings. "
            "LightGBM was chosen mainly for training speed at this row "
            "count and native categorical-feature support without manual "
            "one-hot encoding, a good match for high-cardinality columns "
            "like canal_entrada. Random forests - an older tree-ensemble "
            "approach (bagging instead of boosting), more resistant to "
            "overfitting out of the box but typically leaves accuracy on "
            "the table versus boosting on structured tabular data."
        ),
        watch=(
            "Much easier to overfit than logistic regression given its "
            "flexibility - needs a genuine held-out validation set (Topic "
            "9) and sensible regularization (tree depth, minimum samples "
            "per leaf, learning rate) rather than being trusted on "
            "training-set performance alone."
        ),
        links=[
            ("LightGBM documentation", "https://lightgbm.readthedocs.io/"),
            ("Wikipedia - Gradient boosting", "https://en.wikipedia.org/wiki/Gradient_boosting"),
        ],
        planned=True,
    )

    # ================= CLOSING =================
    pdf.add_page()
    pdf.part_title("Looking Further Ahead (Phase 3-4, not yet detailed)")
    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(*DARK)
    pdf.multi_cell(
        0, 5.6,
        "Two further phases are on the roadmap but not yet designed in "
        "enough detail to document at this depth:",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 10.5)
    x0 = pdf.get_x()
    pdf.cell(4, 5.6, "-")
    pdf.multi_cell(
        pdf.epw - 4, 5.6,
        "Phase 3 plans to use SHAP (Shapley values, from cooperative game "
        "theory) to explain what's actually driving the trained model's "
        "predictions in a way that's faithful to that specific model, "
        "rather than a generic feature-importance heuristic.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_x(x0)
    pdf.cell(4, 5.6, "-")
    pdf.multi_cell(
        pdf.epw - 4, 5.6,
        "Phase 4 will attach a deliberately-labeled simulated "
        "cost-per-contact and value-per-adoption to turn the ranked model "
        "output into an actual targeting recommendation, compared against a "
        "simple business-rule baseline and a contact-everyone baseline.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)
    pdf.learn_more([("SHAP documentation", "https://shap.readthedocs.io/")])

    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(
        0, 5,
        "This document reflects project state as of September 2026 (through "
        "Phase 2's data engineering and its first trained model, a "
        "logistic regression baseline). "
        "For the running, dated log of every concept as it's introduced, "
        "see docs/concepts_log.md in the repository; for the "
        "plain-language project narrative, see Project_Recap.pdf.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
