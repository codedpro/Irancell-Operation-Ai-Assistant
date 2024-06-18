from transformers import TapasTokenizer, TapasForQuestionAnswering
import pandas as pd
from IPython.display import display
import torch

def tapas_question_answer(data, queries):
    model_name = "google/tapas-base-finetuned-wtq"
    model = TapasForQuestionAnswering.from_pretrained(model_name)
    tokenizer = TapasTokenizer.from_pretrained(model_name)

    table = pd.DataFrame.from_dict(data)
    inputs = tokenizer(table=table, queries=queries, padding="max_length", return_tensors="pt")
    outputs = model(**inputs)

    predicted_answer_coordinates, predicted_aggregation_indices = tokenizer.convert_logits_to_predictions(
        inputs, outputs.logits.detach(), outputs.logits_aggregation.detach()
    )

    id2aggregation = {0: "NONE", 1: "SUM", 2: "AVERAGE", 3: "COUNT"}
    aggregation_predictions_string = [id2aggregation[x] for x in predicted_aggregation_indices]

    answers = []
    confidences = []
    for i, coordinates in enumerate(predicted_answer_coordinates):
        confidence = torch.softmax(outputs.logits[i], dim=0).max().item()
        confidences.append(confidence)

        if len(coordinates) == 1:
            answers.append(table.iat[coordinates[0]])
        else:
            cell_values = []
            for coordinate in coordinates:
                cell_values.append(table.iat[coordinate])
            answers.append(", ".join(cell_values))

    results = []
    for query, answer, aggregation, confidence in zip(queries, answers, aggregation_predictions_string, confidences):
        result = {
            "query": query,
            "predicted_answer": answer,
            "aggregation": aggregation,
            "confidence": confidence
        }
        results.append(result)

    return results