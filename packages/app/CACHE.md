## ✅ Claude 3.7 프롬프트 캐시를 위한 캐시포인트 시스템

- 프롬프트 캐시를 위해 캐시포인트를 메시지에 추가해야 한다.
- LLM 은 툴을 이용하여 대화 중에 지정된 섹션의 작성이 완료되면 section_completed 툴을 호출해야 한다.
- section_completed 툴은 해당 섹션의 작성이 완료되었기 때문에 캐시포인트가 생성될 recent_history 의 index 를 cl 의 user_session 에 저장한다.
- 다음 LLM 요청 시 해당 인덱스의 위치에 캐시포인트를 추가해준다.

### 🔧 시스템 구성 요소
- **LLM 모델**: Claude 3.7 (스트리밍 응답 지원)
- **툴 제공 방식**: `bind_tools` (Langchain)
- **툴 역할**: boolean 값을 llm 에서 전달받아 true 이면 캐시포인트 생성
- **실제 캐시 저장 위치**: 사용자 세션 내 캐시 관리

---

### ✅ 캐시포인트 로직

| 항목 | 내용 |
|------|------|
| 캐시포인트 개수 | 최대 **4개** (초과 시 FIFO 방식으로 가장 오래된 것 제거) |
| 캐시포인트 위치 | 시스템 프롬프트, 챕터 5 완료, 챕터 6 완료, 마지막 챕터 완료 |
| 캐시 생성 조건 | 해당 시점의 LLM 응답이 **약 1800 토큰 이상**일 경우에만 생성 |
| 캐시 유지 방식 | 세션에 저장된 캐시를 이후 메시지 빌드 시 프롬프트 앞단에 삽입하여 컨텍스트 유지 |
| 캐시포인트 트리거 | Claude의 스트리밍 응답 마지막 chunk의 metadata 내 툴 호출 여부로 판단 |

### ✅ 섹션 완료 툴 코드

```python
from langchain_core.tools import tool

@tool
def section_completed(section: int) -> bool:
    """
    작성이 완료된 섹션 번호를 받아서 해당 섹션의 작성이 완료되었음을 표시

    Args:
        section (int): 작성이 완료된 섹션 번호, 예시: 5, 6, 11
    Returns:
        bool: 완료 표시 성공 여부
    """
```

### ✅ Chainlit 에서 캐시포인트 처리 방식

- Chainlit 의 경우 캐시포인트가 추가될 때 매칭되는 cl.Message 의 metadata 에 캐시포인트 정보를 추가해준다.
- on_chat_resume hook 에서 cl.Message 의 metadata 에서 캐시포인트 정보를 확인해서 캐시포인트를 복원한다.

### ✅ 처리 흐름 요약

1. LLM이 챕터 종료 등 특정 지점에 도달함
2. 스트리밍 응답 마지막 chunk에서 메타데이터 확인 → 툴 호출 필요 여부 판단
3. 툴(`bind_tools`)은 boolean 값을 llm 에서 전달받아 true 이면 캐시포인트 생성
4. 시스템은:
   - 현재 응답 토큰 수 ≥ 1800 → 캐시 생성
   - 세션에 캐시 저장 (최대 4개 유지)
   - 이후 메시지 빌드 시 캐시를 자동 prepend


<example>
  ```python
  from langchain_core.tools import tool
  from langchain_core.messages import HumanMessage, ToolMessage
  from langchain_aws import ChatBedrockConverse
  import asyncio


  @tool
  def save_game_preference(title: str) -> str:
      """사용자가 게임에 대한 이야기를 하면 게임 제목을 입력받아 사용자의 게임에 대한 선호도를 저장합니다.

      Args:
          title (str): 게임 제목
      Returs:
          bool: 성공 여부
      """
      return True


  async def main():
      llm = ChatBedrockConverse(
          model_id="anthropic.claude-3-sonnet-20240229-v1:0",
          region_name="us-east-1",
      )

      tools = [save_game_preference]

      llm_with_tools = llm.bind_tools(tools)

      query = "워크래프트3 재미있더라. 다른사람들은 어떤지 알아?"
      print(f"User Query: {query}")

      print("\n--- Streaming Initial LLM Response ---")
      first = True
      ai_msg = None

      async for chunk in llm_with_tools.astream([HumanMessage(content=query)]):
          if first:
              ai_msg = chunk
              first = False
          else:
              ai_msg = ai_msg + chunk

          # 스트리밍되는 도구 호출 정보 출력
          if ai_msg.tool_calls:
              print(f"Current tool calls: {ai_msg.tool_calls}")
          if ai_msg.content:
              print(f"Current content: {ai_msg.content}")

          await asyncio.sleep(0)  # 다른 이벤트 루프 작업을 위한 양보

      print("\n--- Complete Initial LLM Response ---")
      print(ai_msg)

      messages = [HumanMessage(content=query), ai_msg]  # Start conversation history

      if not ai_msg.tool_calls:
          print("\n--- LLM did not request any tool calls. Final Answer: ---")
          print(ai_msg.content)
      else:
          for tool_call in ai_msg.tool_calls:
              selected_tool = None
              for t in tools:
                  if t.name == tool_call["name"]:
                      selected_tool = t
                      break

              if selected_tool:
                  tool_output = selected_tool.invoke(tool_call["args"])

                  messages.append(
                      ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
                  )
              else:
                  print(
                      f"Warning: Tool '{tool_call['name']}' requested by LLM but not found."
                  )
                  messages.append(
                      ToolMessage(
                          content=f"Error: Tool '{tool_call['name']}' not found.",
                          tool_call_id=tool_call["id"],
                      )
                  )

          print("\n--- Streaming Final LLM Response ---")
          final_response_content = ""

          async for chunk in llm_with_tools.astream(messages):
              if chunk.content:
                  # content가 리스트인 경우 텍스트 추출
                  if isinstance(chunk.content, list):
                      for content_item in chunk.content:
                          if isinstance(content_item, dict) and "text" in content_item:
                              content_text = content_item.get("text", "")
                              final_response_content += content_text
                              print(content_text, end="", flush=True)
                  # content가 문자열인 경우 그대로 사용
                  else:
                      final_response_content += chunk.content
                      print(chunk.content, end="", flush=True)
              await asyncio.sleep(0)

          print("\n\n--- Complete Final Response ---")
          print(final_response_content)


  if __name__ == "__main__":
      asyncio.run(main())
  ```
</example>