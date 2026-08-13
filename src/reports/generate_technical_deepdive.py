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
        "Prepared August 2026 - covers the reasoning behind Phase 0 and "
        "Phase 1 work, plus the decided (not yet implemented) plan for Phase 2.",
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
        "Sections are grouped by project phase. Part 1 through Part 3 cover "
        "work that is done and verified against real output. Part 4 covers "
        "the Phase 2 plan - genuinely decided, with reasons, but not yet "
        "written as code - and is marked accordingly throughout.",
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
    pdf.part_title("Part 4 - Phase 2 Plan: Building the Model")
    pdf.planned_banner(
        "Everything in this part is a decided plan with real reasoning "
        "behind it, not yet-written code. Treat it as 'here's the plan and "
        "why,' and expect this section to be revised once it's actually "
        "implemented and tested against real results."
    )

    topic_block(
        pdf, 9, "Time-based train/validation split",
        why=(
            "The real use case predicts the future from the past. A random "
            "split would validate the model on rows chronologically mixed "
            "in with training rows, letting validation performance reflect "
            "an unrealistic scenario where the model implicitly benefits "
            "from patterns (macro trends, the declining adoption rate seen "
            "in the Phase 1 EDA) that wouldn't actually be visible yet at "
            "deployment time."
        ),
        how=(
            "Train on the earliest N months, validate on the next month(s) "
            "chronologically - mirroring how the model would actually be "
            "deployed: trained on history, scored on the present."
        ),
        alt=(
            "k-fold cross-validation - scikit-learn's default, excellent for "
            "independent (i.i.d.) rows, the wrong tool here because rows are "
            "not independent across time. TimeSeriesSplit is scikit-learn's "
            "built-in mechanism for the time-respecting version of the same "
            "idea."
        ),
        watch=(
            "Even within a correct time-based split, any preprocessing that "
            "learns something from the data (scaling, imputing missing "
            "values, computing category frequencies) must be fit only on "
            "the training window and then applied to validation - fitting "
            "it on the full dataset first reintroduces leakage even if the "
            "split itself is correct."
        ),
        links=[
            ("scikit-learn - TimeSeriesSplit", "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html"),
        ],
        planned=True,
    )

    topic_block(
        pdf, 10, "Logistic regression as the baseline",
        why=(
            "Before reaching for a more powerful model, the plan is to "
            "establish a simple, fast, fully interpretable baseline. Its "
            "coefficients are directly readable (a one-unit change in a "
            "feature shifts the log-odds of adoption by its coefficient), "
            "making it a genuine sanity check rather than a black box, and "
            "it trains in seconds even at this row count."
        ),
        how=(
            "Models the log-odds of the binary outcome as a linear "
            "combination of the input features; a sigmoid function converts "
            "that linear score into a probability between 0 and 1."
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
            "between each feature and the log-odds of the outcome. The "
            "Phase 1 EDA already found a non-monotonic, inverted-U "
            "relationship for age - a plain linear term won't capture that "
            "well. That's a concrete, EDA-driven reason a more flexible "
            "model is also being tried, not just modeling fashion."
        ),
        links=[("scikit-learn - Linear Models (logistic regression)", "https://scikit-learn.org/stable/modules/linear_model.html")],
        planned=True,
    )

    topic_block(
        pdf, 11, "Gradient-boosted trees (LightGBM) as the stronger model",
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
        "This document reflects project state as of August 2026 (through "
        "the end of Phase 1). For the running, dated log of every concept "
        "as it's introduced, see docs/concepts_log.md in the repository; "
        "for the plain-language project narrative, see Project_Recap.pdf.",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
