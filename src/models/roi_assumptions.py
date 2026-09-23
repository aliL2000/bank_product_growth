"""Phase 4 simulated ROI assumptions - the single source of truth for every
cost/value/uplift number used in the targeting ROI comparison.

These are SIMULATED assumptions, not real bank economics
(docs/decisions/005-simulated-roi-assumptions.md). Profit for contacting a
list of K customers:

    profit = uplift * adopters_captured * value_per_adoption - K * cost_per_contact

Uplift is relative: contact raises each contacted customer's adoption chance
by `uplift` (e.g. 0.20 = 20%), so incremental adoptions = uplift * adopters
the list actually contains. The dataset has no treatment/control structure,
so this can't be measured here - it's assumed, and swept for sensitivity.
"""

# Base case (decision record 005).
COST_PER_CONTACT = 0.50  # EUR, email/in-app channel
VALUE_PER_ADOPTION = 150.0  # EUR, first-year net margin of one new card
UPLIFT = 0.20  # relative increase in adoption chance from being contacted

# Sensitivity sweep values - reported alongside the base case, never instead of it.
COST_SWEEP = {"email": 0.50, "phone": 6.00}
VALUE_SWEEP = [50.0, 150.0, 300.0]
UPLIFT_SWEEP = [0.05, 0.10, 0.20, 0.40]


def break_even_precision(cost_per_contact=COST_PER_CONTACT,
                         value_per_adoption=VALUE_PER_ADOPTION,
                         uplift=UPLIFT):
    """Precision a contact list needs for its simulated profit to be >= 0.

    Each contact earns uplift * value on average for every adopter it hits,
    so a list with precision p earns p * uplift * value per contact against
    a cost of cost_per_contact: profitable iff p >= cost / (uplift * value).
    """
    return cost_per_contact / (uplift * value_per_adoption)


def simulated_profit(n_contacted, adopters_captured,
                     cost_per_contact=COST_PER_CONTACT,
                     value_per_adoption=VALUE_PER_ADOPTION,
                     uplift=UPLIFT):
    """Simulated net profit (EUR) of contacting n_contacted customers, of whom
    adopters_captured actually adopted."""
    incremental_adoptions = uplift * adopters_captured
    return incremental_adoptions * value_per_adoption - n_contacted * cost_per_contact
