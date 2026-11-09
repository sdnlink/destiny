import { lazy } from "react";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import BaziPage from "./pages/BaziPage";
import ConsultModulePage from "./pages/ConsultModulePage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import WorkflowRoute from "./pages/WorkflowRoute";
import ZiweiPage from "./pages/ZiweiPage";

const FengshuiPanel = lazy(() => import("./components/fengshui/FengshuiPanel"));

// 卜筮 / 时空类共用「输入 + 结果」外壳，按 moduleKey 渲染各自的独立页面
const CONSULT_ROUTES = ["zhouyi", "meihua", "liuyao", "qimen", "liuren"];

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          {CONSULT_ROUTES.map((key) => (
            <Route key={key} path={key} element={<ConsultModulePage moduleKey={key} />} />
          ))}
          <Route path="bazi" element={<BaziPage />} />
          <Route path="ziwei" element={<ZiweiPage />} />
          <Route path="fengshui" element={<FengshuiPanel />} />
          <Route path="workflow" element={<WorkflowRoute />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
