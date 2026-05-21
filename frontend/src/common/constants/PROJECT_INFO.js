export const projecttype = [
  {
    value: "建筑工程项目",
    label: "建筑工程项目",
  },
  {
    value: "市政工程项目",
    label: "市政工程项目",
  },
  {
    value: "房地产",
    label: "房地产",
  },
  {
    value: "工业厂房",
    label: "工业厂房",
  },
  {
    value: "基础设施",
    label: "基础设施",
  },
];

export const pjcolumns = [
  {
    id: "pjname",
    label: "项目名称",
    minWidth: 170,
  },
  {
    id: "pjnumber",
    label: "项目编号",
    minWidth: 170,
    format: (value) => value.toLocaleString("en-US"),
  },
  {
    id: "pjtype",
    label: "项目类型",
    minWidth: 170,
  },
  {
    id: "pjmanager",
    label: "负责人",
    minWidth: 170,
  },
];

