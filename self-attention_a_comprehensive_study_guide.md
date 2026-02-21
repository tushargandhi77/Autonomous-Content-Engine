# Self-Attention: A Comprehensive Study Guide

## Understanding the Fundamentals of Self-Attention

Self-attention enables a model to weigh different input elements for contextual understanding. It uses three core vectors:
*   **Query (Q):** Represents the element seeking context.
*   **Key (K):** Represents elements available to provide context.
*   **Value (V):** The information content associated with each Key.
Q interacts with K to determine attention scores, which then weight V to form a contextualized output.

The **scaled dot-product attention** mechanism computes these scores as `softmax((Q @ K.T) / sqrt(d_k)) @ V`. Here, `Q @ K.T` measures similarity. Dividing by `sqrt(d_k)` (the scaling factor) prevents large values from destabilizing the subsequent `softmax` normalization, ensuring stable training. These normalized scores then weight the Value vectors.

```python
import torch
import math

def scaled_dot_product_attention(q, k, v, mask=None):
    d_k = q.size(-1)
    scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(d_k)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9) # Prevents attention to masked positions
    attention_weights = torch.softmax(scores, dim=-1)
    output = torch.matmul(attention_weights, v)
    return output
```

An **attention mask** prevents information leakage (e.g., seeing future tokens in decoder models) and handles variable sequence lengths (ignoring padding tokens). Applied *before* softmax, it sets scores for irrelevant positions to a very large negative number, effectively zeroing them out after `softmax`.

---
**Mini-Quiz:**
What are the two main reasons for using an attention mask?

## Implementing and Analyzing Self-Attention

For an input sequence, each token generates Query (Q), Key (K), and Value (V) vectors by multiplying with learned weight matrices. Attention weights are then derived by taking the scaled dot product of a token's Q with all other K's, followed by a softmax function. These weights determine how much each V vector contributes to the final output for that token.

Self-attention processes all tokens in parallel, a significant departure from sequential Recurrent Neural Networks (RNNs). This parallelization enables much faster computation and allows self-attention to directly capture long-range dependencies between any two tokens, overcoming limitations like vanishing gradients often found in RNNs.

A key performance consideration for self-attention is its quadratic computational complexity, O(N^2), where N is the sequence length. This can become computationally expensive for very long sequences. To mitigate this, techniques like sparse attention (where not all token pairs compute attention) or local attention (restricting attention to a defined neighborhood of tokens) are employed.

**Practice Prompt:**
Consider a sequence of 1000 tokens. If the sequence length doubles to 2000 tokens, how does the computational cost for self-attention change? What practical approach could you use for extremely long sequences to manage this cost?

## Review, Advanced Topics, and Key Takeaways

**Practice Prompt:** For the sentence "The `bank` of the river was steep, but the financial `bank` was secure," how does self-attention distinguish between the `bank` meanings? What's a primary limitation when processing extremely long sequences?

**Multi-head attention** enhances the core mechanism by running attention in parallel "heads," each with independent parameters. Each head learns to capture diverse contextual relationships simultaneously. (Think of multiple specialized lenses, each highlighting a different feature).

This powerful mechanism is fundamental to modern **Transformer models**. Its ability to model long-range dependencies and enable parallel processing has driven state-of-the-art performance in deep learning's sequence modeling tasks, from natural language processing to computer vision.
