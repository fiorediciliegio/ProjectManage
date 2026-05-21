import { useSearchParams } from "react-router-dom";

const useProjectParams = () => {
  const [searchParams] = useSearchParams();
  const projectName = searchParams.get("projectName");
  const projectId = searchParams.get("projectId");

  return { projectName, projectId };
};

export default useProjectParams;

