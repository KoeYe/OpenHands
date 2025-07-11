import { useEffect } from "react";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "#/store";
import { useConversationId } from "#/hooks/use-conversation-id";
import {
  initialState as browserInitialState,
  setUrl,
} from "#/state/browser-slice";

/**
 * 将原本只能查看截图的 BrowserPanel 改造成可交互的 iframe 浏览器。
 * 逻辑：
 * 1. 每次切换 conversation 时仍重置为 initialState.url。
 * 2. 组件渲染一个顶部只读的 url 栏 + iframe。
 * 3. 当需要更换地址时，只需在其他地方 dispatch(setUrl(newUrl)) 即可，iframe 会自动刷新。
 */
export function BrowserPanel() {
  const { url } = useSelector((state: RootState) => state.browser);
  const { conversationId } = useConversationId();
  const dispatch = useDispatch();

  // 切换会话时重置 URL（保持现有行为）
  useEffect(() => {
    dispatch(setUrl(browserInitialState.url));
  }, [conversationId]);

  return (
    <div className="h-full w-full flex flex-col text-neutral-400">
      {/* 顶部地址栏 */}
      <div className="w-full p-2 truncate border-b border-neutral-600">
        {url}
      </div>

      {/* 可交互 iframe */}
      <iframe
        key={url} // url 变化时重新加载页面
        src={url}
        title="browser-frame"
        className="w-full h-full grow border-none rounded-b-xl"
      />
    </div>
  );
}
