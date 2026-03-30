from ..models import CriterionSchema, ReviewSchema

review_schema = ReviewSchema()
criterion_schema = CriterionSchema(many=True)


def dump_review_with_markable_criteria(review):
    payload = review_schema.dump(review)
    # Keep FK id fields available even when schema omits include_fk.
    payload["assignmentID"] = review.assignmentID
    payload["reviewerID"] = review.reviewerID
    payload["revieweeID"] = review.revieweeID

    criteria_rows = review.criteria.order_by("id").all()
    criteria_payload = criterion_schema.dump(criteria_rows)
    for entry, row in zip(criteria_payload, criteria_rows):
        entry["criterion_row"] = {
            "id": row.criterion_row.id,
            "question": row.criterion_row.question,
            "scoreMax": row.criterion_row.scoreMax,
            "hasScore": row.criterion_row.hasScore,
        }

    payload["criteria"] = criteria_payload
    payload["review_window_open"] = review.is_review_window_open()
    payload["is_complete"] = review.completion_status()
    return payload


def dump_received_review_anonymized(review):
    payload = dump_review_with_markable_criteria(review)
    payload["reviewer"] = {"id": 0, "name": "Anonymous"}
    payload["reviewer_anonymous"] = True
    return payload


def split_reviews_by_type(reviews, dump_fn):
    return {
        "peer_reviews": [
            dump_fn(review)
            for review in reviews
            if review.review_type != "group"
        ],
        "group_reviews": [
            dump_fn(review)
            for review in reviews
            if review.review_type == "group"
        ],
    }
