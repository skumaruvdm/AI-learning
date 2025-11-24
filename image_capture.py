
import requests
import json
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class Metadata:
    width: int
    height: int

@dataclass
class BoundingBox:
    x: int
    y: int
    w: int
    h: int

@dataclass
class Value:
    text: str
    confidence: float
    boundingBox: BoundingBox

@dataclass
class DenseCaptionResult:
    values: List[Value]

@dataclass
class AnalyzeResult:
    modelVersion: str
    metadata: Metadata
    denseCaptionsResult: DenseCaptionResult

@dataclass
class AnalyzeRequest:
    uri: str

class DenseCaption:
    def generate_dense_caption(self):
        # For prod environment, please find the endpoint and resource key of your computer vision resource from Azure portal.
        endpoint = "<API-Endpoint>"
        url = f"{endpoint}computervision/imageanalysis:analyze?features=denseCaptions&gender-neutral-caption=false&api-version=2023-10-01"
        key = "<Resource-Key>"

        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Content-Type': 'application/json; charset=utf-8'
        }

        # with image url
        image_url = "https://ai.azure.com/common/vision/denseCaptioning/DenseCaptioningSample2.png"

        # Create an instance of the AnalyzeRequest class
        analyze_request = AnalyzeRequest(uri=image_url)

        # Serialize the instance to a dictionary
        json_data = asdict(analyze_request)

        response = requests.post(url, headers=headers, json=json_data)
        response_content = response.text

        # Print the JSON response for debugging
        print("Response Content:", response_content)

        # Deserialize and print the result
        data = json.loads(response_content)
        try:
            deserialized_object = self.from_dict(AnalyzeResult, data)

            print(f"Model Version: {deserialized_object.modelVersion}")
            print(f"Metadata - Width: {deserialized_object.metadata.width}, Height: {deserialized_object.metadata.height}")
            for value in deserialized_object.denseCaptionsResult.values:
                print(f"Caption: {value.text}, Confidence: {value.confidence}")
                print(f"BoundingBox - X: {value.boundingBox.x}, Y: {value.boundingBox.y}, Width: {value.boundingBox.w}, Height: {value.boundingBox.h}")
        except KeyError as e:
            print(f"KeyError: {e}. Please check the JSON response structure.")

    def from_dict(self, data_class, data):
        if isinstance(data, list):
            return [self.from_dict(data_class.__args__[0], item) for item in data]
        if isinstance(data, dict):
            fieldtypes = {f.name: f.type for f in data_class.__dataclass_fields__.values()}
            return data_class(**{k: self.from_dict(fieldtypes[k], v) for k, v in data.items()})
        return data

# Usage example
if __name__ == "__main__":
    denseCaption = DenseCaption()
    denseCaption.generate_dense_caption()