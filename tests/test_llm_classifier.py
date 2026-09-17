from cloudserve_support.llm_classifier import LLMClassifier


class FakeLLMClient:
    def complete(self, system_prompt, user_prompt):
        return '{"intent": "deployment_failure", "urgency": "high", "confidence": 0.95}'


def test_llm_classifier():
    classifier = LLMClassifier(client=FakeLLMClient())

    result = classifier.classify("My deployment failed.")

    assert result.intent == "deployment_failure"
    assert result.urgency == "high"
    assert result.confidence == 0.95
