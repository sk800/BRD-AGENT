import time

import pytest
from sentence_transformers import SentenceTransformer

from brd_agent.ingestion.pipeline.chunking.recursive import (
    structure_aware_recursive,
)


PRODUCTION_MODEL_CONFIGS = [
    ("BGE-small", "BAAI/bge-small-en-v1.5", 384),
]

PRODUCTION_QUERIES = [
    ("How can a student register for a course?", ("course registration",)),
    ("Who can update student records?", ("administrator permissions",)),
    (
        "What happens when attendance falls below the threshold?",
        ("attendance notifications",),
    ),
    ("How are outstanding fees paid and confirmed?", ("fee payments",)),
    ("Which security control protects student information?", ("security",)),
    ("What response time is required for the student portal?", ("performance",)),
    ("Which reports should administrators receive?", ("reporting",)),
    ("How does the system notify students?", ("notifications",)),
]

def realistic_brd_elements():
    sections = [
        (
            "Course Registration",
            "Students shall browse available courses, submit registration requests, and drop a course before the registration deadline. The system shall validate eligibility and prevent duplicate registrations.",
        ),
        (
            "Administrator Permissions",
            "Administrators shall create and update student records, manage course capacity, approve registration exceptions, and deactivate accounts. Students may view their own records but cannot edit them.",
        ),
        (
            "Attendance Notifications",
            "Faculty members shall record attendance after each class. The system shall calculate attendance percentages and send a notification to students when attendance falls below the required threshold.",
        ),
        (
            "Fee Payments",
            "Students shall view outstanding fees and pay online using the supported payment gateway. The system shall generate a payment confirmation, retain transaction history, and prevent duplicate charges.",
        ),
        (
            "Security",
            "The system shall enforce role-based access control, encrypt sensitive student information in transit and at rest, and record an audit event for changes to academic or payment records.",
        ),
        (
            "Performance",
            "The student portal shall return normal page requests within two seconds for at least 500 concurrent users. Background report generation may run asynchronously.",
        ),
        (
            "Reporting",
            "Administrators shall generate enrollment, attendance, and fee collection reports. Reports shall support date filters, export to CSV, and a downloadable PDF summary.",
        ),
        (
            "Notifications",
            "The system shall send registration decisions, payment confirmations, attendance warnings, and password-reset messages through email and in-app notifications.",
        ),
        (
            "Availability and Recovery",
            "The service shall be available during business hours, perform daily backups, and restore transactional data within four hours after a critical failure.",
        ),
        (
            "Audit and Compliance",
            "Audit records shall include the actor, action, timestamp, and affected record. Audit logs shall be retained for at least one year and must be accessible only to authorized administrators.",
        ),
    ]
    elements = []
    for order, (heading, content) in enumerate(sections, start=1):
        elements.extend(
            [
                {
                    "element_id": f"brd-heading-{order}",
                    "type": "heading",
                    "content": heading,
                    "location": {"source": "realistic-brd", "order": order},
                },
                {
                    "element_id": f"brd-requirement-{order}",
                    "type": "paragraph",
                    "content": content,
                    "location": {"source": "realistic-brd", "order": order},
                },
            ]
        )
    return elements


def _format_texts(model_name, texts, is_query):
    return texts


def benchmark_embeddings(model, model_name, chunks):
    texts = [
        chunk["text"]
        for chunk in chunks
        if chunk.get("text", "").strip()
    ]

    start = time.perf_counter()

    embeddings = model.encode(
        _format_texts(model_name, texts, is_query=False),
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    elapsed = time.perf_counter() - start

    texts_per_second = (
        len(texts) / elapsed
        if elapsed > 0
        else 0
    )

    print("\n" + "=" * 60)
    print(f"{model_name} EMBEDDING BENCHMARK")
    print("=" * 60)
    print(f"Model                 : {model_name}")
    print(f"Number of chunks      : {len(texts)}")
    print(f"Embedding dimension   : {embeddings.shape[1]}")
    print(f"Embedding time        : {elapsed:.6f} seconds")
    print(f"Chunks per second     : {texts_per_second:.2f}")
    print("=" * 60)

    return texts, embeddings


def retrieval_metrics(scores, texts, evaluation_queries):
    reciprocal_ranks = []
    recall_at_1 = 0
    recall_at_3 = 0
    ndcg_at_3 = []

    for query_index, (_, relevance_phrases) in enumerate(evaluation_queries):
        relevant_indices = {
            index
            for index, text in enumerate(texts)
            if any(phrase in text.lower() for phrase in relevance_phrases)
        }
        ranking = scores[query_index].argsort()[::-1]
        relevant_ranks = [
            rank + 1
            for rank, index in enumerate(ranking)
            if index in relevant_indices
        ]
        reciprocal_ranks.append(1 / relevant_ranks[0] if relevant_ranks else 0)
        recall_at_1 += int(bool(set(ranking[:1]) & relevant_indices))
        recall_at_3 += int(bool(set(ranking[:3]) & relevant_indices))

        dcg = sum(
            1 / (rank + 1)
            for rank, index in enumerate(ranking[:3])
            if index in relevant_indices
        )
        ideal_relevance_count = min(len(relevant_indices), 3)
        ideal_dcg = sum(1 / (rank + 1) for rank in range(ideal_relevance_count))
        ndcg_at_3.append(dcg / ideal_dcg if ideal_dcg else 0)

    return {
        "recall_at_1": recall_at_1 / len(evaluation_queries),
        "recall_at_3": recall_at_3 / len(evaluation_queries),
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks),
        "ndcg_at_3": sum(ndcg_at_3) / len(ndcg_at_3),
    }


@pytest.mark.slow
@pytest.mark.parametrize(
    "display_name,model_name,expected_dimension",
    PRODUCTION_MODEL_CONFIGS,
)
def test_production_embedding_retrieval_on_real_brd_documents(
    display_name,
    model_name,
    expected_dimension,
):
    elements = realistic_brd_elements()
    chunks = structure_aware_recursive(
        elements,
        chunk_size=300,
        chunk_overlap=40,
    )
    chunks = [chunk for chunk in chunks if chunk.get("text", "").strip()]

    model = SentenceTransformer(model_name)
    start = time.perf_counter()
    texts, embeddings = benchmark_embeddings(model, model_name, chunks)
    corpus_seconds = time.perf_counter() - start

    query_texts = _format_texts(
        model_name,
        [query for query, _ in PRODUCTION_QUERIES],
        is_query=True,
    )
    query_start = time.perf_counter()
    query_embeddings = model.encode(
        query_texts,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    query_seconds = time.perf_counter() - query_start
    metrics = retrieval_metrics(
        query_embeddings @ embeddings.T,
        texts,
        PRODUCTION_QUERIES,
    )
    vector_storage_kb = embeddings.shape[0] * embeddings.shape[1] * 4 / 1024

    print(f"\n{display_name} PRODUCTION EVALUATION")
    print("Documents             : 1 realistic BRD evaluation corpus")
    print(f"Chunks                : {len(texts)}")
    print(f"Corpus latency        : {corpus_seconds:.4f}s")
    print(f"Query latency         : {query_seconds:.4f}s")
    print(f"Vector storage        : {vector_storage_kb:.2f} KB (float32)")
    print(f"Recall@1              : {metrics['recall_at_1']:.2%}")
    print(f"Recall@3              : {metrics['recall_at_3']:.2%}")
    print(f"MRR                   : {metrics['mrr']:.4f}")
    print(f"nDCG@3                : {metrics['ndcg_at_3']:.4f}")

    assert embeddings.shape[1] == expected_dimension
    assert embeddings.shape[0] == len(texts) > 0
    assert metrics["recall_at_3"] >= 0.80