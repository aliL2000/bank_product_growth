"""Generate reports/Project_Recap.pdf — a plain-language project recap for a
non-ML audience. Content mirrors ROADMAP.md's Working Log; rerun this script
after updating the roadmap to keep the recap in sync.

Usage: python src/reports/generate_project_recap.py
"""

from pathlib import Path

from fpdf import FPDF

OUT_PATH = Path(__file__).resolve().parents[2] / "reports" / "Project_Recap.pdf"

TEAL = (16, 94, 107)
DARK = (30, 41, 59)
GRAY = (100, 110, 120)
BOX_BG = (237, 242, 245)
BOX_BORDER = (16, 94, 107)
BADGE_BG = (16, 94, 107)


class Recap(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, text):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(*TEAL)
        self.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
        y = self.get_y()
        self.set_draw_color(*TEAL)
        self.set_line_width(0.6)
        self.line(self.l_margin, y, self.l_margin + 22, y)
        self.ln(4)

    def body(self, text, size=10.5, color=DARK, style=""):
        self.set_font("Helvetica", style, size)
        self.set_text_color(*color)
        self.multi_cell(0, 5.6, text, align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10.5)
        self.set_text_color(*DARK)
        self.cell(4, 5.6, "-")
        self.multi_cell(
            self.epw - 4, 5.6, text, align="L", new_x="LMARGIN", new_y="NEXT"
        )

    def callout(self, title, text):
        self.ln(1)
        pad = 3
        self.set_font("Helvetica", "B", 10)
        title_lines = self.multi_cell(
            self.epw - 2 * pad, 5.2, title, dry_run=True, output="LINES"
        )
        self.set_font("Helvetica", "", 10)
        body_lines = self.multi_cell(
            self.epw - 2 * pad, 5.2, text, dry_run=True, output="LINES"
        )
        box_h = pad * 2 + 5.2 * (len(title_lines) + len(body_lines))
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*BOX_BG)
        self.set_draw_color(*BOX_BORDER)
        self.set_line_width(0.8)
        self.rect(x, y, self.epw, box_h, style="DF")
        self.set_xy(x + pad, y + pad)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*TEAL)
        self.multi_cell(
            self.epw - 2 * pad, 5.2, title, align="L", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_x(x + pad)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK)
        self.multi_cell(
            self.epw - 2 * pad, 5.2, text, align="L", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_xy(x, y + box_h + 4)

    def numbered_step(self, n, title, body_text):
        self.ln(1)
        x, y = self.get_x(), self.get_y()
        d = 7
        self.set_fill_color(*BADGE_BG)
        self.ellipse(x, y, d, d, style="F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(255, 255, 255)
        self.set_xy(x, y + 0.9)
        self.cell(d, d - 1, str(n), align="C")
        self.set_xy(x + d + 3, y)
        self.set_font("Helvetica", "B", 11.5)
        self.set_text_color(*DARK)
        self.multi_cell(
            self.epw - d - 3, 6, title, align="L", new_x="LMARGIN", new_y="NEXT"
        )
        self.set_x(self.l_margin)
        self.ln(1)
        self.body(body_text)


def build():
    pdf = Recap(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(20, 18, 20)

    # --- Page 1: title + big picture ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 12, "Product Adoption & Growth Analytics", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(
        0, 6,
        "A plain-language recap of the project so far - written for someone new to "
        "machine learning",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.multi_cell(
        0, 5,
        "Prepared September 2026 - covers sessions from project kickoff "
        "through the end of Phase 3 (explainability and segment "
        "identification)",
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(4)

    pdf.section_title("The Big Picture")
    pdf.body(
        "Imagine you work at a bank. The bank sells lots of different products: "
        "checking accounts, savings accounts, credit cards, mortgages, investment "
        "funds, and more. Most customers only use a handful of these products, "
        "even though some of them would genuinely benefit from a product they "
        "don't have yet."
    )
    pdf.body(
        "The bank can't realistically call, email, or advertise to every single "
        "customer about every single product every month - that's expensive, and "
        "it annoys people who get pitched things they'll never want. So the real "
        "business question is:"
    )
    pdf.set_font("Helvetica", "BI", 11)
    pdf.set_text_color(*TEAL)
    pdf.multi_cell(
        0, 6,
        '"Out of all our existing customers, who is actually likely to want a '
        'specific product next - and can we focus our limited marketing effort '
        'on them instead of everyone?"',
        align="L", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(2)
    pdf.body(
        "This project builds a system to answer that question for one specific "
        "product (a credit card), using real, anonymized data from a Spanish "
        'bank. In machine learning terms, this is called a "propensity model" - '
        "a model that estimates how likely someone is to do something (in this "
        "case, adopt a new product) based on what we already know about them."
    )
    pdf.callout(
        "Why this matters for learning ML:",
        "This kind of problem - ranking customers by likelihood of an action, "
        "with a limited budget to act on - shows up constantly in real jobs: "
        "who's likely to cancel their subscription (churn), who's likely to "
        "click an ad, who's likely to default on a loan. It's one of the most "
        "common, practical applications of machine learning in business.",
    )

    # --- Page 2: dataset ---
    pdf.add_page()
    pdf.section_title("The Dataset")
    pdf.body(
        "We're using a public dataset from Santander (a real bank), originally "
        "released for a Kaggle data science competition. A few key facts about it:"
    )
    pdf.bullet("About 13.6 million rows and roughly 950,000 unique customers.")
    pdf.bullet(
        '17 monthly "snapshots" of the bank\'s customers, from January 2015 to '
        "June 2016 - so the same customer appears multiple times, once per "
        "month, like a repeated survey."
    )
    pdf.bullet(
        "Each row records ~24 things about the customer (age, tenure with the "
        "bank, income, activity level, etc.) plus 24 yes/no flags for which "
        "products they currently hold."
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 7, "Why this dataset, specifically?", new_x="LMARGIN", new_y="NEXT")
    pdf.body(
        "It's real, messy data - not a cleaned-up textbook example. It has "
        "missing values, inconsistent categories, and customers who come and go, "
        "which is exactly what you'd deal with at a real job. It also happens to "
        "have the one structural feature this project absolutely needs: because "
        "it's the same customers tracked month after month, we can actually see "
        "when someone newly picks up a product - which is the whole basis for "
        "the prediction target."
    )
    pdf.callout(
        "Features vs. Label (two terms you'll see constantly in ML):",
        '"Features" are the inputs the model gets to look at (a customer\'s age, '
        'income, how many products they already have, etc.). The "label" is the '
        "correct answer we're trying to teach the model to predict (did this "
        "customer adopt a credit card next month: yes or no). Training a model "
        "is basically: show it lots of examples of features paired with the "
        "correct label, and let it find the statistical patterns that connect "
        "them.",
    )

    # --- Page 3+: steps ---
    pdf.add_page()
    pdf.section_title("What We've Actually Done, Step by Step")
    pdf.body(
        "Below is every real step taken so far, in order, explained in plain "
        'terms along with the reasoning behind it - not just "what" but "why."'
    )

    pdf.numbered_step(
        1,
        "Set up the project structure (before touching any data)",
        "Before writing any analysis code, we built a clean folder structure: "
        "separate places for raw data, processed data, code, reports, and "
        'documentation, plus a README and a roadmap. We also started a '
        '"decision log" - a folder where any significant choice gets written '
        "down with its reasoning.\n\n"
        "Why: this is the equivalent of drawing up a blueprint before building "
        "a house. On a real team, if everyone just writes code and notebooks "
        "with no structure, nobody (including future-you) can find anything or "
        "reconstruct why a decision was made. Writing decisions down as you "
        "make them is far easier and more honest than trying to remember your "
        "reasoning weeks later - and it's exactly what makes a project readable "
        "to someone else, like an interviewer.",
    )
    pdf.numbered_step(
        2,
        "Downloaded the data and verified it landed correctly",
        "Once the two data files were in place, we didn't just assume they "
        "were fine - we checked file sizes, counted rows, and confirmed the "
        "columns matched what was expected (48 columns: 24 profile columns + "
        "24 product flags).\n\n"
        'Why: this is a "trust but verify" habit. A corrupted download or a '
        "file that got cut off partway through is a common, boring failure "
        "that's very cheap to catch early and very annoying to catch after "
        "you've already built analysis on top of bad data.",
    )
    pdf.numbered_step(
        3,
        "Scanned the full file safely, without overloading the computer's memory",
        "The full data file is 2.29 GB on disk. Naively loading it entirely "
        "into memory with all 48 columns would have used roughly 15 GB of RAM "
        "- close enough to this computer's available memory to be risky. So "
        'instead of loading everything at once, the data was read in "chunks" '
        "of 500,000 rows at a time, tallying up statistics (like missing-value "
        "counts) as it went, and never holding more than one chunk in memory "
        "at once.",
    )
    pdf.callout(
        "Chunking, explained simply:",
        "Imagine trying to summarize a 1,000-page book, but you can only hold "
        "20 pages in your head at once. You'd read 20 pages, jot down notes, "
        "forget those pages, then read the next 20, and so on - adding to the "
        "same running notes the whole time. That's exactly what \"chunked "
        "reading\" does with a huge data file: process a manageable slice, "
        "keep a running tally, move on, and never need the whole book in your "
        "head simultaneously.",
    )
    pdf.body(
        "What we found: two columns were almost entirely empty (over 99.8% "
        'missing - not useful), the customer\'s income ("renta") was missing '
        "about 20.5% of the time (needs a thoughtful fix later, since income "
        "likely matters for who buys a credit card), and a cluster of "
        "unrelated-looking columns were all missing at exactly the same rate "
        "- a strong hint they're missing for the same underlying reason "
        "(probably brand-new customers whose very first monthly record is "
        "incomplete)."
    )

    pdf.add_page()
    pdf.numbered_step(
        4,
        'Picked which product to actually predict ("Service A")',
        "The dataset has 24 possible products we could try to predict "
        "adoption of. We had narrowed it to three realistic candidates: a "
        "credit card, a payroll account, or a mutual fund (investment "
        "product). We picked the credit card.",
    )
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.set_text_color(*DARK)
    pdf.cell(0, 6, "Why credit card, specifically:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.5)
    pdf.bullet(
        "Only about 3.7% to 5.8% of customers hold a credit card in any given "
        'month - meaning roughly 94-96% of customers are potential targets, '
        'which gives the model plenty of both "yes" and "no" examples to '
        "learn from."
    )
    pdf.bullet(
        "It's a product the bank can actually influence with marketing and "
        "outreach. A payroll account, by contrast, is mostly adopted because "
        "someone changed employers - something no amount of bank marketing "
        'can cause - which would have made the whole "targeting strategy" '
        "part of this project less meaningful."
    )
    pdf.bullet(
        "It's likely to correlate with a wide mix of other signals already in "
        "the data (activity level, income, how many other products someone "
        "has), giving the model more to actually learn from."
    )
    pdf.ln(1)
    pdf.body(
        "This reasoning, along with the real prevalence numbers behind it, "
        "was written up as a formal decision record in the project's docs "
        'folder - so if anyone (including us, months from now) wonders "why '
        'credit card and not investments?", the answer is documented, not '
        "just remembered."
    )

    pdf.numbered_step(
        5,
        'Built the "adoption label" - the actual target the model will learn to predict',
        "This is the most technically important step so far. For every "
        "customer, in every month, we needed to answer one specific question: "
        "did this customer NOT have a credit card last month, but DOES have "
        'one this month? If yes, that\'s an "adoption event" - the thing we '
        "eventually want a model to predict in advance.\n\n"
        'The naive way to do this in code is to sort each customer\'s rows by '
        'month and just grab "the previous row." But that\'s a subtle trap: '
        "about 7.1% of customer-month records don't have a record from "
        "exactly one month before (because that customer joined partway "
        "through, or had a gap where they temporarily left the bank's radar). "
        'If you just grab "the previous row" positionally, you might '
        "accidentally compare March to January and think it's "
        "March-vs-February - silently producing a wrong answer with no error "
        "message.\n\n"
        "To avoid that, each row was matched to its true previous month using "
        "an exact date-based match (customer ID + calendar month), and any "
        'row where no true "last month" record existed was explicitly marked '
        "as unknown, rather than guessed at.",
    )
    pdf.callout(
        "The single most important finding from this step:",
        "Only about 0.57% of eligible customer-months resulted in an actual "
        "adoption event (69,118 adoptions out of about 12.1 million eligible "
        "customer-months). In other words, adopting a credit card in any "
        "given month is rare - roughly 1 in every 175 eligible customers.",
    )
    pdf.body(
        'Why this matters a lot for what comes next: imagine a lazy model '
        'that just always predicts "no, this customer will not adopt a '
        "credit card.\" That model would be right 99.43% of the time - and "
        "completely useless, since it never identifies anyone to target. "
        'This is called "class imbalance," and it\'s exactly why the '
        'project\'s success metric was chosen up front to be "precision at '
        'K" (out of the top K customers the model ranks as most likely, how '
        "many actually adopt?) rather than plain accuracy. A rare-event "
        "problem needs a ranking-based grading system, not a simple "
        "right/wrong percentage."
    )

    # --- Step 6: EDA ---
    pdf.add_page()
    pdf.numbered_step(
        6,
        "Looked for patterns: does adoption change over time, or by who the customer is?",
        "With the label in hand, the next step was exploratory data analysis "
        "(EDA) - looking at the data to find patterns, before building any "
        "predictive model. Two questions: does the adoption rate change over "
        "the 17-month window, and does it differ by customer characteristics "
        "like age, how long they've been a customer, income, or how active "
        "they are?",
    )
    pdf.callout(
        "A subtlety worth calling out: using \"before\" information, not \"after\":",
        "To compare adoption rates by, say, income, you need to know each "
        "customer's income. The tempting shortcut is to use their income from "
        "the same month they adopted the card - but that's information from "
        "*after* the fact, and a customer's profile can shift slightly around "
        "the time they pick up a new product. So instead, every comparison "
        "below uses each customer's information from the month *before* they "
        "could have adopted - the same information a real targeting decision "
        "would actually have access to. Using \"after the fact\" information "
        "by mistake is called \"leakage,\" and it's one of the most common "
        "ways a model ends up looking far more accurate in testing than it "
        "will ever be in real use.",
    )
    pdf.body(
        "What we found, in plain terms:"
    )
    pdf.bullet(
        "Over time: the monthly adoption rate roughly halved across the "
        "17-month window, from around 0.8% in mid-2015 down to around 0.45% "
        "by early-mid 2016, with no strong seasonal pattern."
    )
    pdf.bullet(
        "Whether a customer is currently \"active\" with the bank "
        "(the activity index) was the single biggest differentiator found: "
        "active customers adopted at about 50 times the rate of inactive "
        "ones (1.28% vs. 0.03%)."
    )
    pdf.bullet(
        "The bank's own customer segment label (a VIP-style \"TOP\" tier vs. "
        "regular retail customers vs. students) showed a more than 30x "
        "spread - the TOP segment adopted at about 3.0%, versus roughly 0.1% "
        "for students."
    )
    pdf.bullet(
        "How long someone has been a customer (tenure) mattered a lot too: "
        "adoption climbed steadily from about 0.1% for customers with under "
        "6 months' history to about 1.4% for customers of 20+ years - a "
        "roughly 13x spread, and a clean, steady relationship rather than a "
        "noisy one."
    )
    pdf.bullet(
        "Income and age also mattered, but more modestly: higher-income "
        "customers adopted at roughly 2.4 times the rate of lower-income "
        "ones, and adoption rose with age up to the 40-50 bracket before "
        "declining again for older customers."
    )
    pdf.body(
        "Along the way, a few data-quality quirks were also flagged for "
        "later cleanup: a small number of rows have an obviously-wrong "
        "placeholder value for tenure, and some ages in the raw data are "
        "implausible (over 160 years old) - both need explicit handling "
        "before they're used to train a model, rather than being silently "
        "ignored the way this exploratory pass did."
    )
    pdf.callout(
        "Why this step matters for what comes next:",
        "This is the step where you start to see, in plain terms, which "
        "pieces of information are worth giving a model. Activity level, "
        "tenure, and customer segment all look like strong candidates for "
        "the first real predictive model in Phase 2; income and age look "
        "like real but secondary signals. Full numbers are written up in "
        "reports/01_eda_findings.md and the underlying notebook.",
    )

    # --- Step 7: train/val split ---
    pdf.add_page()
    pdf.numbered_step(
        7,
        "Split the data by time, so testing honestly reflects the real job",
        "Before building any model, the data has to be split into a chunk "
        "it learns from (\"train\") and a chunk used only to check how well "
        "it actually did (\"validation\"). The obvious approach - shuffle "
        "all the rows randomly and split - would be a mistake here.",
    )
    pdf.callout(
        "Why not just shuffle and split randomly?",
        "The same customer shows up in many consecutive months, and their "
        "attributes (tenure, income, activity) barely change month to "
        "month. A random split could put a customer's March row in "
        "training and their April row in validation - so the model would "
        "effectively get a sneak peek at a near-duplicate of the answer "
        "during training, making it look far more accurate than it will "
        "ever be once it's scoring genuinely new, future months in real "
        "use.",
    )
    pdf.body(
        "Instead, the split was made by calendar month: the last 3 months "
        "of labeled data (March-May 2016) became validation, and every "
        "earlier month became training - no shuffling, no randomness. This "
        "mirrors the real situation the model will eventually face: trained "
        "on the past, judged on how well it predicts a future it hasn't "
        "seen."
    )

    # --- Step 8: first feature group ---
    pdf.add_page()
    pdf.numbered_step(
        8,
        "Started building the model's actual inputs, one group at a time",
        "With the split in place, the next job is \"feature engineering\": "
        "turning raw columns into clean, well-behaved inputs a model can "
        "actually learn from. Rather than doing all of it in one giant "
        "step, this is being built as a handful of focused groups - the "
        "first covers tenure (how long someone's been a customer) and "
        "activity level, the two strongest signals found back in the EDA.",
    )
    pdf.body(
        "This meant fixing two real data-quality issues head-on rather than "
        "letting them pass through silently: a placeholder value the raw "
        "data uses for \"tenure unknown\" (a nonsense number, -999999) had "
        "to be converted to a proper \"missing\" marker, and the small "
        "number of genuinely missing values (about 0.16% of rows) were "
        "filled in using a fair, honest method - explained in the callout "
        "below - rather than just being dropped or guessed at."
    )
    pdf.callout(
        "Filling in missing values without \"cheating\":",
        "When a value is missing, a common fix is to fill it with a typical "
        "value - e.g., the median tenure across everyone. But if that "
        "typical value is computed using validation-month data too, the "
        "validation set has quietly influenced its own scoring, which is "
        "the same kind of unfair sneak-peek problem the time-based split "
        "was built to prevent. So the fill-in value is computed using "
        "*only* training months, then applied the same way to both "
        "training and validation rows. A second column also records which "
        "rows were originally missing, so the model can still tell \"a "
        "typical customer\" apart from \"we didn't actually know.\"",
    )
    pdf.body(
        "The remaining feature groups planned for this phase - how many "
        "other products a customer already holds, which channel they joined "
        "through, and basic demographics like income and customer segment - "
        "follow the same pattern and are the immediate next step."
    )

    # --- Step 9: product count + demographics ---
    pdf.add_page()
    pdf.numbered_step(
        9,
        "Added two more feature groups: how many products someone already "
        "has, and basic demographics",
        "The second feature group counts how many of the bank's other "
        "products (out of ~23, deliberately not counting the credit card "
        "itself) a customer already holds. The third adds demographics: "
        "age, sex, the bank's own customer-segment label, and income.\n\n"
        "For income specifically (about 20% missing in the raw data), a "
        "flat \"fill in the typical value for everyone\" approach felt too "
        "crude, since typical income genuinely differs a lot by customer "
        "segment. So missing income is filled in using the typical income "
        "*for that customer's own segment*, not one number for the whole "
        "bank - and a small number of extreme high earners (income data "
        "like this always has some) are handled with a standard "
        "\"log transform,\" which compresses very large values without "
        "changing their relative order, so a handful of outliers don't "
        "distort the typical pattern the model sees.",
    )
    pdf.callout(
        "The single biggest finding of the whole project so far:",
        "How many other products a customer already holds turned out to be "
        "by far the strongest signal found: customers with 6 or more other "
        "products adopt a credit card at roughly 60 times the rate of "
        "customers with none. Intuitively, this makes sense - someone who "
        "already trusts the bank with several products is a much easier "
        "sell on one more than someone who barely uses the relationship.",
    )

    # --- Step 10: audit / eligibility-filter bug catch ---
    pdf.numbered_step(
        10,
        "Caught and fixed a subtle bug by deliberately self-auditing the work",
        "Partway through, a structured self-review of the project (asking, "
        "in effect, \"where would a skeptical outside reviewer poke "
        "holes?\") found a real problem: about 4.5% of the rows being used "
        "still belonged to customers who already had a credit card before "
        "the month in question. For those rows, \"did not adopt\" is "
        "meaningless - they couldn't newly adopt something they already "
        "had - so those rows were quietly diluting every pattern found so "
        "far, including the \"60 times\" number above (which was actually "
        "stronger, not weaker, once the fix went in).",
    )
    pdf.callout(
        "Why this is a good sign, not a bad one:",
        "Catching your own mistake before it reaches a stakeholder is "
        "exactly the point of building in deliberate review checkpoints "
        "rather than assuming a first pass is correct. The fix was made at "
        "the earliest possible point in the process (the train/validation "
        "split itself), so every downstream file automatically inherited "
        "the correction instead of needing separate patches everywhere.",
    )

    # --- Step 11: 3-way split ---
    pdf.add_page()
    pdf.numbered_step(
        11,
        "Added a third, completely hands-off \"test\" set",
        "Up to this point, data was split two ways: a training set to "
        "learn from, and a validation set to check performance. But this "
        "project plans to try more than one model (logistic regression, "
        "then a more powerful technique) and compare them on that same "
        "validation set - and using the very same data both to *pick the "
        "best model* and to *report its final performance* would make the "
        "final number a bit too optimistic, since some of that "
        "\"performance\" is really just having gotten lucky in a way that "
        "happens to suit the validation set specifically.\n\n"
        "The fix: split into three pieces instead of two. Train (the "
        "earliest 11 months) to learn from, validation (the next 2 months) "
        "to compare and choose between models, and test (the final 3 "
        "months) - set aside and not looked at again until the very end, "
        "when the honestly best model gets graded on it exactly once.",
    )

    # --- Step 12: modeling table assembly ---
    pdf.numbered_step(
        12,
        "Assembled every piece into one ready-to-use table",
        "All of the pieces built so far - the train/validation/test split, "
        "the adoption label, and all three feature groups - were combined "
        "into a single table: 12,111,689 rows (one per eligible customer "
        "per month) and 23 columns. Every merge was double-checked to make "
        "sure it didn't accidentally duplicate or drop any rows along the "
        "way, since a single silent mistake at this assembly step would "
        "quietly corrupt everything built on top of it.",
    )

    # --- Step 13: baseline model ---
    pdf.add_page()
    pdf.numbered_step(
        13,
        "Trained the first real predictive model",
        "With everything assembled, the project trained its first actual "
        'model: logistic regression. In plain terms, it works like a '
        "weighted checklist - it looks at everything known about a "
        "customer, assigns each fact a learned point value (positive facts "
        "push the score up, negative facts push it down), adds all the "
        "points together, and converts that total into an estimated "
        "probability of adoption.\n\n"
        "It was deliberately trained first, before anything more "
        "sophisticated, because it's simple enough to read directly: you "
        "can look at exactly which facts it decided matter and by how "
        "much, and check that against everything already learned from "
        "exploring the data. It passed that check - activity level and "
        "product count came out as strongly positive, and age traced the "
        "same peaks-in-middle-age pattern found earlier, rather than "
        "anything surprising or suspicious.",
    )
    pdf.callout(
        "What the results actually mean, in plain terms:",
        "Handed one random customer who did adopt a credit card and one "
        "random customer who didn't, the model correctly identifies which "
        "one is the real adopter about 91% of the time - a common way to "
        "grade how well a model separates the two groups. More practically: "
        "if the bank could only afford to contact its top 1% "
        "highest-scored customers, that group would actually go on to "
        "adopt at roughly 15 times the rate you'd get by picking customers "
        "at random - a first, real signal that this approach could "
        "meaningfully outperform a scattershot marketing campaign.",
    )
    pdf.body(
        "One more thing had to be handled to get here: adoption is rare "
        "(about 0.6% of customer-months), so a model left to its own "
        'devices could get away with just always guessing "no" and still '
        "be right 99.4% of the time - while being completely useless for "
        "actually finding anyone to target. A standard technique called "
        "class weighting was used to force the model to treat a missed "
        "real adopter as a much costlier mistake than a missed non-adopter, "
        "so it's actually incentivized to tell the two groups apart."
    )

    # --- Step 14: LightGBM ---
    pdf.add_page()
    pdf.numbered_step(
        14,
        "Trained a second, more powerful model",
        "Logistic regression's weighted checklist is simple and readable, "
        "but it can only really combine facts in a straight-line way. The "
        "project's second model, LightGBM, works differently: imagine a "
        "series of specialists reviewing the same customer one after "
        "another, where each new specialist's entire job is to catch the "
        "mistakes the specialists before them collectively made. Their "
        "combined judgment becomes the final prediction. This lets the "
        "model pick up on patterns the checklist approach can't, like "
        '"age matters, but in a peaks-in-the-middle way" or "tenure '
        'matters more for customers who are currently active" - without '
        "anyone having to spell those patterns out by hand.",
    )
    pdf.callout(
        "A real snag hit along the way:",
        "A standard trick for rare-event problems (give the rare outcome "
        "more weight, used successfully on the first model) was tried here "
        "too - and it backfired. It made this model's training process "
        "stop improving after a single round, mistaking early noise for "
        "having already found the best answer. Removing the trick let "
        "training actually run properly, and the model ended up doing "
        "better without it. The lesson: a technique that helps one kind of "
        "model can quietly break a structurally different one, and it's "
        "worth checking, not assuming.",
    )
    pdf.body(
        "Result: this model correctly identifies the real adopter, when "
        "compared against a non-adopter, about 92% of the time (versus the "
        "first model's 91%) - a real but modest improvement, with "
        '"currently active" as its single most relied-upon fact.'
    )

    # --- Step 15: formal test evaluation ---
    pdf.add_page()
    pdf.numbered_step(
        15,
        "Formally graded both models on the data neither had ever seen",
        "For months, this project had deliberately kept one slice of data "
        '("test") completely untouched, precisely so it could be used for '
        "one honest, final grade instead of a practice-round estimate. "
        "This step scored both models against that untouched slice, "
        "exactly once, and compared them the way the business would "
        'actually use them: "if we can only contact our top X% of '
        'customers by predicted likelihood, how many of them really do '
        'adopt?"',
    )
    pdf.callout(
        "The real finding here mattered more than the numbers themselves:",
        "During earlier practice-round comparisons, the second model "
        "(LightGBM) looked like the clear winner. On the untouched test "
        "data - the grade that actually counts - the two models turned out "
        "to be essentially tied, and the simpler first model was even "
        "slightly ahead at a couple of budget levels. The practice round "
        "had fewer real adoption examples to compare against, so part of "
        'the earlier "LightGBM wins" impression was just noise, not a real '
        "advantage. This is exactly the kind of overconfident, too-early "
        "conclusion that keeping data genuinely untouched is meant to "
        "catch.",
    )
    pdf.body(
        "Headline result: contacting the bank's top 1% most-likely-scored "
        "customers reaches roughly 1 in 6 of everyone who would actually "
        "adopt that quarter, with about 1 in 12 of those contacted turning "
        "out to be a real adopter - a ~17x improvement over calling the "
        "same number of customers at random. This result closed out Phase "
        "2 of the project."
    )

    # --- Step 16: SHAP explainability ---
    pdf.add_page()
    pdf.numbered_step(
        16,
        "Explained exactly what drives an individual prediction",
        "A model like LightGBM doesn't have one readable checklist the way "
        "logistic regression does - it's built from 36 of the "
        '"specialists" from Step 14, working together. To open that up, '
        "the project used a technique called SHAP, which has a "
        "mathematical guarantee: for any single customer, it splits their "
        "predicted score into exactly how much each individual fact about "
        "them pushed the prediction up or down - and those pieces add up "
        "precisely to the real prediction (checked by hand across 1.75 "
        "million customers, accurate to a tiny fraction of a percent).",
    )
    pdf.body(
        "The result was a genuine surprise: the single biggest driver of a "
        "specific prediction turned out to be whether the customer is "
        "currently active with the bank - not how many products they "
        "already hold, which had looked like the strongest single pattern "
        "back in Step 6's exploration, and not their age, which needed the "
        "most internal adjustments from the model to get right. Three "
        "different ways of measuring \"what matters most\" each gave a "
        "different #1 answer - explained in full in "
        "reports/03_explainability_segments.md - because each one is "
        "really answering a slightly different question. SHAP's answer is "
        "the one to trust for \"what actually moves a real prediction,\" "
        "since it's the only one of the three that's a verified, exact "
        "breakdown of the model's own output rather than a rough proxy for "
        "it."
    )

    # --- Step 17: calibration check ---
    pdf.add_page()
    pdf.numbered_step(
        17,
        "Checked whether the model's confidence can actually be trusted",
        'A model saying "this customer is 99.9997% likely to adopt" sounds '
        "impressive - but is that number actually earned, or is it an "
        "overstatement? This step checked: among the customers the model "
        "was most confident about, does the real, observed adoption rate "
        "actually back that confidence up?",
    )
    pdf.callout(
        "What was found:",
        "For the tiniest sliver of most-confident customers (the top "
        "0.01%, about 175 people), the model was about 12.6x overconfident "
        "- it predicted around 43% on average, but the real observed rate "
        "was closer to 3%. That overconfidence faded fast: by the top 1-5% "
        "of customers, which is the realistic range a real marketing "
        "budget would actually use, the model's confidence matched reality "
        "closely.",
    )
    pdf.body(
        "Practical takeaway carried into the next step: it's fine to trust "
        'the model\'s group-level averages and its overall ranking, but a '
        "single customer's extreme individual score - especially "
        'somewhere in the very top sliver - shouldn\'t be quoted or acted '
        "on at face value."
    )

    # --- Step 18: segment identification ---
    pdf.add_page()
    pdf.numbered_step(
        18,
        "Found a specific, real customer segment worth prioritizing",
        "The last piece of this phase turned everything learned so far "
        'into something actionable: which specific group of customers '
        "should the bank actually prioritize for credit card outreach? "
        'The two conditions that matter - "under-served" (doesn\'t have '
        'many bank products yet) and "high-propensity" (likely to say '
        'yes) - turned out to genuinely pull against each other, since '
        "Step 16 found that holding more products is one of the strongest "
        "signals of adopting another one. So instead of comparing "
        "under-served customers to the whole customer base (which found "
        "nothing useful), the project compared under-served customers "
        "against each other - who, among people with few products, "
        "converts relatively well?",
    )
    pdf.callout(
        "The segment found:",
        "Customers who are currently active, in the bank's \"particulares\" "
        "customer segment, already hold exactly one product, and are aged "
        "35-64. This group converts to credit card holders at roughly 5x "
        "the rate of other similar one-product customers - and it's a "
        "large, real group (over 110,000 customers in just this sample), "
        "not a fluke. A statistical technique that specifically discounts "
        "patterns found in small, unreliable samples (rather than just "
        "trusting a raw percentage) was used to confirm this wasn't just "
        "luck.",
    )
    pdf.body(
        "This closed out Phase 3, and gives Phase 4 a concrete, plain-"
        "English targeting rule to compare against the model's raw score."
    )

    # --- Final page: status + next ---
    pdf.add_page()
    pdf.section_title("Where We Are Now, and What's Next")
    pdf.body(
        "Every step above is committed to the project's version control "
        "history (git), with a written explanation attached to each commit, "
        "and the repository is live on GitHub. At this point:"
    )
    pdf.bullet("The problem is defined: predict which existing customers will newly adopt a credit card.")
    pdf.bullet("The dataset is verified, understood, and its data-quality issues are documented.")
    pdf.bullet('The prediction target ("Service A") is decided and justified with real numbers.')
    pdf.bullet(
        "The label - the actual right-answer column the model will eventually "
        "be trained on - exists as a processed data file, built carefully to "
        "avoid a subtle but easy-to-miss bug."
    )
    pdf.bullet(
        "The exploratory analysis is done: adoption rate over time and by "
        "customer segment, with activity level, tenure, and customer segment "
        "standing out as the strongest patterns found so far."
    )
    pdf.bullet(
        "The data is split three ways - training, validation, and a "
        "completely untouched test set - by calendar month rather than "
        "randomly, so the eventual final grade is honest."
    )
    pdf.bullet(
        "All planned feature groups are built and cleaned: tenure, "
        "activity level, how many other products a customer already holds "
        "(the strongest single signal found), and demographics (age, sex, "
        "customer segment, income)."
    )
    pdf.bullet(
        "A subtle data-quality bug (some already-existing cardholders "
        "incorrectly counted as \"chose not to adopt\") was caught and "
        "fixed via a deliberate self-review, before it could quietly "
        "distort any model trained on it."
    )
    pdf.bullet(
        "Two models were trained and formally compared on data neither had "
        "ever seen: logistic regression and LightGBM turned out to be "
        "essentially tied, with the top 1% highest-scored customers "
        "adopting at roughly 17 times the rate you'd get by contacting "
        "customers at random."
    )
    pdf.bullet(
        "The winning model's predictions were opened up and explained: "
        "whether a customer is currently active with the bank is the "
        "single biggest driver of an individual prediction - a genuine "
        "surprise, since it wasn't the strongest pattern found in earlier "
        "exploration."
    )
    pdf.bullet(
        "The model's confidence was checked against reality, not just "
        "trusted: it's accurate in the realistic 1-5% outreach range, but "
        "overconfident for the tiny sliver of its single most-confident "
        "predictions - so individual extreme scores aren't taken at face "
        "value."
    )
    pdf.bullet(
        "A specific, real customer segment worth prioritizing was found: "
        "active, single-product customers aged 35-64 in the bank's "
        '"particulares" segment, who convert to credit card holders at '
        "roughly 5x the rate of similar customers - large enough (over "
        "110,000 customers in this sample) to be a genuine target, "
        "confirmed with a statistical check against it being a fluke."
    )
    pdf.ln(1)
    pdf.set_font("Helvetica", "B", 11.5)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Phases 1 through 3 are complete.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*TEAL)
    pdf.cell(0, 7, "Next up", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.body(
        "Phase 4: attach a deliberately-labeled, simulated cost-per-contact "
        "and value-per-adoption to turn the model's ranking - and the "
        "segment found in Step 18 - into an actual targeting "
        "recommendation, comparing model-score targeting, the plain-"
        "English business rule found above, and a contact-everyone "
        "baseline."
    )
    pdf.set_font("Helvetica", "I", 9.5)
    pdf.set_text_color(*GRAY)
    pdf.multi_cell(
        0, 5,
        "A note on honesty about limitations: this is Spanish retail banking "
        "data from 2015-2016, so none of the specific numbers here (adoption "
        "rates, etc.) would transfer directly to a different bank or a "
        "different time period. The point of this project is to demonstrate "
        "the methodology - how to responsibly go from a business question to "
        "a data-backed targeting recommendation - not to claim these exact "
        "figures apply anywhere else.",
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    build()
