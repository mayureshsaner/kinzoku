from flask import Flask, request, jsonify, render_template
import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

app = Flask(__name__)

# Ensure you secure your API key in production (e.g., os.environ.get("GEMINI_API_KEY"))
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)


class TargetAudience(BaseModel):
    primary_persona: str = Field(description="Specific, hyper-niched description of the ideal user.")
    core_pain_point: str = Field(description="The exact daily frustration this user experiences.")


class StageOneStrategy(BaseModel):
    clarified_problem: str = Field(description="A crisp, 1-sentence definition of the exact market problem.")
    value_proposition: str = Field(description="The core differentiator.")
    audience: TargetAudience
    uniqueness: int = Field(description="Calculate a uniqueness percentage, based on comparing with existing players.")
    follow_up_questions: List[str] = Field(
        description="You MUST generate exactly 3 aggressive, challenging questions to expose flaws in the business model. NEVER leave this empty.")
    list_of_competitors: List[str] = Field(description="Drop the Active competitors in the market.")
    founders_background: List[str] = Field(description="Founders background of the respective competitor brands.")
    self_made_rating: int = Field(
        description="Rate on the scale of 10 about self-made capability of making this particular business field.")


class StageStrategy2(BaseModel):
    brand_name: list[str] = Field(description="3 distinct brand name options")
    color_code: str = Field(description="Main brand color hex code")
    brand_voice: str = Field(description="Instructions on how the brand speaks")


class RegeneratedNames(BaseModel):
    new_names: list[str] = Field(description="3 completely new, distinct, and highly creative brand name options.")


class StageStrategy3(BaseModel):
    visual_language: str = Field(
        description="Which visual language fits the audience? Describe typography, imagery, and UI feel.")
    voice_and_messaging: str = Field(
        description="What voice and messaging stay consistent? Outline the core messaging pillars.")
    market_entry_strategy: str = Field(
        description="How should the brand enter the market? Provide a concise, actionable launch tactic.")


class Competitor(BaseModel):
    name: str
    x_score: int = Field(description="Score from 0 to 100 on the X axis")
    y_score: int = Field(description="Score from 0 to 100 on the Y axis")


class PositioningMap(BaseModel):
    x_axis_low: str = Field(description="e.g., Budget, Slow, Traditional")
    x_axis_high: str = Field(description="e.g., Premium, Fast, Modern")
    y_axis_low: str = Field(description="e.g., Mass Market, Complex")
    y_axis_high: str = Field(description="e.g., Niche, Simple")
    competitors: list[Competitor]
    your_brand_x: int
    your_brand_y: int


class SharkTankEvaluation(BaseModel):
    investor_persona: str = Field(
        description="The specific 'Shark' archetype responding (e.g., Aggressive Tech Titan, The Retail King).")
    brutal_feedback: str = Field(
        description="Harsh, direct feedback on the business model, valuation, or market viability.")
    decision: str = Field(description="The final verdict: Either 'I am OUT' or 'I will offer X for Y% equity'.")


class PersonaChatResponse(BaseModel):
    reply: str = Field(description="The conversational reply from the perspective of the target persona.")
    interest_level: int = Field(
        description="Score from 0 to 100 on how likely they are to buy/use it based on the pitch.")


@app.route('/', methods=['GET'])
def index():
    return render_template('answer.html')


@app.route('/stage1', methods=['POST'])
def stage1():
    try:
        data = request.get_json()
        customer_idea = data.get('idea', '')

        stage_one_prompt = f"""
        ROLE: Act as a ruthless, elite Startup Advisor conducting an intake interview.
        CONTEXT: A founder has pitched you this concept: "{customer_idea}". 
        TASK: Extract the true market problem, define a hyper-specific target audience, and articulate the value proposition. If the idea is broad, generate 2-3 aggressive follow-up questions.
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents={'text': stage_one_prompt},
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StageOneStrategy,
            ),
        )

        parsed_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        return jsonify({"stage1": parsed_dict})

    except Exception as e:
        print(f"🔥 PYTHON ERROR IN STAGE 1: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/stage2', methods=['POST'])
def stage2():
    try:
        data = request.get_json()
        prompt_for_stage2 = f"""
        Act as a Creative Director. You are building a brand for this specific audience:
        Audience: {data.get('primary_persona')}
        Core Problem: {data.get('core_pain_point')}
        Value Proposition: {data.get('value_proposition')}

        Based strictly on this strategy, generate 3 brand names, a primary hex color, and a brand voice.
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents={'text': prompt_for_stage2},
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StageStrategy2,
            ),
        )

        parsed_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        return jsonify({"stage2": parsed_dict})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/regenerate-names', methods=['POST'])
def regenerate_names():
    try:
        data = request.get_json()
        regen_prompt = f"""
        Act as a Creative Director. You are building a brand for this specific audience:
        Audience: {data.get('primary_persona')}
        Core Problem: {data.get('core_pain_point')}
        Value Proposition: {data.get('value_proposition')}

        The founder rejected these previous names: {data.get('previous_names')}.
        Based strictly on this strategy, generate 3 COMPLETELY DIFFERENT brand names.
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents={'text': regen_prompt},
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=RegeneratedNames,
            ),
        )
        parsed_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        return jsonify(parsed_dict)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stage3', methods=['POST'])
def stage3():
    try:
        data = request.get_json()
        prompt_for_stage3 = f"""
        Act as a Chief Marketing Officer. Develop a Go-To-Market and Brand Strategy for this startup:
        Audience: {data.get('primary_persona')}
        Value Proposition: {data.get('value_proposition')}
        Selected Brand Name: {data.get('brand_name')}
        Brand Color: {data.get('color_code')}

        Answer these exactly:
        1. Which visual language fits the audience?
        2. What voice and messaging stay consistent?
        3. How should the brand enter the market?
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents={'text': prompt_for_stage3},
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=StageStrategy3,
            ),
        )

        parsed_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        return jsonify({"stage3": parsed_dict})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/shark-tank', methods=['POST'])
def shark_tank():
    try:
        data = request.get_json()
        idea = data.get('idea')

        prompt = f"""
        Act as a ruthless, elite venture capitalist evaluating a pitch for a high-stakes competition like IIT Bombay Eureka.
        The founder's idea: {idea}

        Provide a brutal, unvarnished assessment of the business model, unit economics, or market necessity.
        Conclude with a definitive investment decision.
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents={'text': prompt},
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SharkTankEvaluation,
            ),
        )

        parsed_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        return jsonify({"shark_tank": parsed_dict})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/persona-chat', methods=['POST'])
def persona_chat():
    try:
        data = request.get_json()
        persona = data.get('persona')
        pain_point = data.get('pain_point')
        message = data.get('message')

        prompt = f"""
        Act strictly as this target audience persona: "{persona}".
        Your core daily frustration is: "{pain_point}".

        A founder just pitched you this: "{message}"

        Respond in character (first person). Be honest. Are you skeptical? Excited? Does this actually solve your problem?
        """

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents={'text': prompt},
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PersonaChatResponse,
            ),
        )

        parsed_dict = response.parsed.model_dump() if hasattr(response.parsed, 'model_dump') else response.parsed.dict()
        return jsonify({"chat": parsed_dict})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
