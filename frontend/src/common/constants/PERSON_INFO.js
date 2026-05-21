export const personroles = [
  { value: "项目经理", label: "项目经理" },
  { value: "生产经理", label: "生产经理" },
  { value: "技术总工", label: "技术总工" },
  { value: "安全经理", label: "安全经理" },
  { value: "商务经理", label: "商务经理" },
  { value: "材料主管", label: "材料主管" },
  { value: "资料主管", label: "资料主管" },
  { value: "综合办主任", label: "综合办主任" },
  { value: "工程师", label: "工程师" },
  { value: "技术员", label: "技术员" },
  { value: "质量员", label: "质量员" },
  { value: "预算员", label: "预算员" },
  { value: "安全员", label: "安全员" },
  { value: "资料员", label: "资料员" },
  { value: "施工员", label: "施工员" },
];

export const percolumns = [
  {
    id: "pername",
    label: "姓名",
    minWidth: 170,
  },
  {
    id: "pernumber",
    label: "人员编号",
    minWidth: 170,
    format: (value) => value.toLocaleString("en-US"),
  },
  {
    id: "perrole",
    label: "职位",
    minWidth: 170,
  },
  {
    id: "permail",
    label: "邮箱",
    minWidth: 170,
  },
];

