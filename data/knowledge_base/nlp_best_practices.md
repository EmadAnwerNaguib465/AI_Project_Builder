# NLP: Best Practices and Architecture Guide

## Overview

Natural Language Processing (NLP) enables machines to understand, generate, and manipulate human language. The field has been transformed by Transformer-based models since 2017. Modern NLP is dominated by Large Language Models (LLMs) and fine-tuning strategies.

## Core NLP Tasks

**Text Classification**: Assigning a label to text. Subtypes: sentiment analysis, topic classification, spam detection, intent recognition. Best models: BERT, RoBERTa, DeBERTa for fine-tuning; GPT-4o for zero-shot.

**Named Entity Recognition (NER)**: Extracting structured entities (persons, organizations, locations, dates) from text. Best models: bert-base-NER, spaCy large models, GLiNER.

**Text Summarization**: Extractive (select sentences) vs. Abstractive (generate new text). Models: BART, Pegasus, T5, LLAMA for abstractive; TextRank for extractive.

**Machine Translation**: Sequence-to-sequence translation. Models: mBART, NLLB-200 (Meta, 200 languages), Helsinki-NLP MarianMT models.

**Question Answering (QA)**: Extractive QA (span from document) vs. Generative QA. Models: DeBERTa for extractive, GPT-4o/Gemini for generative, RAG systems for knowledge-grounded QA.

**Text Generation**: Generating coherent text from a prompt. Models: GPT-4o, Gemini, Claude, Mistral, LLAMA 3.

## Transformer Architecture Fundamentals

All modern NLP models are based on the Transformer architecture (Attention Is All You Need, 2017):
- **Encoder models (BERT family)**: Best for understanding tasks (classification, NER, QA extraction)
- **Decoder models (GPT family)**: Best for generation tasks (text generation, summarization)
- **Encoder-Decoder (T5, BART)**: Best for sequence-to-sequence tasks (translation, summarization)

## Fine-Tuning Strategy

For most NLP classification tasks with labeled data (> 100 examples):

1. Choose a pretrained model from Hugging Face Hub matching your task
2. Add a task-specific head (linear layer for classification)
3. Fine-tune with AdamW optimizer, linear warmup + cosine decay schedule
4. Learning rate: 2e-5 to 5e-5 for BERT-sized models
5. Batch size: 16-32 (accumulate gradients if GPU memory limited)
6. Training epochs: 3-5 for classification (early stopping on validation loss)

**Data requirements**: Fine-tuning BERT needs as few as 100-500 labeled examples for simple classification. For NER, you need 1000-5000 annotated sentences. For complex generation, you need thousands.

## Zero-Shot and Few-Shot Approaches

When labeled data is scarce:

- **Zero-shot classification**: Use GPT-4o or Gemini with carefully crafted prompts. No fine-tuning needed.
- **Few-shot prompting**: Provide 3-10 examples in the prompt for in-context learning.
- **Cross-encoder reranking**: Use a pretrained cross-encoder to rank candidates.
- **SetFit**: Few-shot fine-tuning with contrastive learning on sentence-transformers. Works with only 8 examples per class.

## Key Public Datasets

- **GLUE / SuperGLUE**: Multi-task benchmarks for classification and NLU
- **SQuAD 2.0**: 150K Q&A pairs from Wikipedia (reading comprehension)
- **SST-2**: 67K movie review sentences for sentiment (binary)
- **CoNLL-2003**: NER benchmark for English (4 entity types)
- **AG News**: 120K news articles, 4 classes (text classification)
- **IMDb Reviews**: 50K movie reviews (binary sentiment)
- **Common Crawl**: Petabyte-scale web corpus for pretraining

## Evaluation Metrics

- **Classification**: Accuracy, Macro F1, Weighted F1, MCC
- **NER**: Token-level F1, Entity-level F1 (strict and partial)
- **Generation**: BLEU, ROUGE-1/2/L, BERTScore, human evaluation
- **QA**: Exact Match, F1 (word overlap)

## Recommended Tech Stack

- **Pretrained Models**: Hugging Face Transformers (50,000+ models)
- **Training Framework**: PyTorch + Hugging Face Trainer or LightningAI
- **Data Processing**: Hugging Face Datasets, spaCy, NLTK
- **Tokenization**: Hugging Face Tokenizers (fast, Rust-based)
- **Embeddings**: sentence-transformers for semantic similarity
- **Serving**: FastAPI + ONNX Runtime, Hugging Face Inference Endpoints
- **Experiment Tracking**: WandB, MLflow

## Production Considerations

- Always evaluate on a held-out test set, never on validation
- Monitor for label drift and concept drift in production
- Use confidence thresholds to route low-confidence predictions for human review
- For multilingual tasks: use multilingual models (mBERT, XLM-RoBERTa)
- Quantization: Use bitsandbytes for 4-bit/8-bit quantization on large models
