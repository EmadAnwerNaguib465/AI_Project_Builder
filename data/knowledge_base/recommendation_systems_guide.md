# Recommendation Systems: Architecture and Best Practices

## Overview

Recommendation Systems (RecSys) help users discover relevant items from large catalogs. They are used in e-commerce (Amazon), streaming (Netflix, Spotify), social media (TikTok, Instagram), and news aggregation. Modern recommendation systems combine multiple approaches.

## Types of Recommendation Systems

### 1. Collaborative Filtering (CF)
Based on user-item interaction patterns (ratings, clicks, purchases). "Users who liked X also liked Y."

- **User-based CF**: Find similar users, recommend what they liked
- **Item-based CF**: Find similar items to what the user liked
- **Matrix Factorization**: Decompose user-item matrix into latent factors (SVD, ALS)
- **Neural CF (NCF)**: Use neural networks to learn user-item interactions

**Strength**: No item content needed. **Weakness**: Cold start problem for new users/items.

### 2. Content-Based Filtering
Recommend items similar to what the user has liked, based on item features.

- User profile built from item features (genre, author, keywords, embeddings)
- Item similarity computed via cosine similarity or dot product
- Works for text (TF-IDF, embeddings) and structured features

**Strength**: No cold start for new items. **Weakness**: Limited to known user preferences.

### 3. Hybrid Systems (Industry Standard)
Combine CF and content-based to get the best of both:
- Weighted hybrid: combine scores from both systems
- Cascade: use one as pre-filter, other as reranker
- Feature augmentation: use content features as input to CF model

### 4. Session-Based Recommendations
Recommend based on the current session's interaction sequence (no user history needed):
- GRU4Rec: Recurrent network over item sequences
- BERT4Rec: BERT-based masked item prediction
- SASRec: Self-attention sequential recommendation

## Key Algorithms and Models

| Algorithm | Type | Best For |
|-----------|------|----------|
| SVD / ALS | Matrix Factorization | Dense user-item matrices |
| BPR (Bayesian Personalized Ranking) | Matrix Factorization | Implicit feedback |
| LightGCN | Graph Neural Network | Social networks, rich interactions |
| BERT4Rec | Transformer | Session-based, sequential |
| Wide & Deep | Neural CF | Large-scale, many features |
| DeepFM | Factorization Machine | Click-through rate prediction |
| Two-Tower Model | Dual encoder | Large-scale retrieval |

## Architecture: Two-Stage Pipeline

Modern large-scale recommendation systems use a two-stage pipeline:

**Stage 1: Candidate Generation (Retrieval)**
- Goal: Retrieve hundreds of candidates from millions of items quickly
- Method: Approximate Nearest Neighbor (ANN) search with learned item embeddings
- Models: Two-Tower (user + item encoders), MIPS (Maximum Inner Product Search)
- Tools: FAISS, ScaNN, Annoy

**Stage 2: Ranking (Re-ranking)**
- Goal: Rank the candidates with a more powerful model
- Method: Feature-rich model with user context, item features, and interaction history
- Models: LightGBM, XGBoost, Wide & Deep, DeepFM
- Latency budget: 50-100ms

## Cold Start Solutions

- **New users**: Use popular items, trending content, or ask for explicit preferences onboarding
- **New items**: Use content-based features until interaction data accumulates
- **Hybrid fallback**: Fall back to content-based or popularity-based for cold items

## Key Datasets

- **MovieLens 25M**: 25M ratings, 162K users, 62K movies — explicit feedback
- **Amazon Reviews (2023)**: 571M reviews across product categories — implicit + explicit
- **Yelp Dataset**: 7M reviews, 150K businesses — business recommendations
- **Netflix Prize**: 100M ratings, 480K users — matrix factorization benchmark
- **LastFM**: Music listening history — sequential recommendation

## Evaluation Metrics

- **Accuracy**: RMSE, MAE (for explicit ratings)
- **Ranking**: Precision@K, Recall@K, NDCG@K, MAP@K, MRR
- **Beyond Accuracy**: Diversity, Novelty, Serendipity, Coverage
- **Business**: Click-through rate, conversion rate, watch time (A/B test)

## Recommended Tech Stack

- **Traditional**: Surprise library (SVD, KNN), implicit (BPR, ALS)
- **Deep Learning**: PyTorch Geometric (graph-based), Transformers4Rec
- **Large Scale**: Apache Spark MLlib, TensorFlow Recommenders (TFRS)
- **Serving**: Redis (feature store), FAISS (vector search), FastAPI
- **Experiment**: A/B testing with statistical significance (>95%)
- **Feature Store**: Feast, Tecton, Hopsworks
