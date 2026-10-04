export type Requirement = {
  id: string;
  name: string;
  description: string;
  required: boolean;
  severity: "critical" | "warning";
};

export type ProductConfig = {
  name: string;
  category: string;
  imageUrl: string;
  requirements: Requirement[];
};

export type Detection = {
  id: string;
  label: string;
  confidence: number;
  category: "object" | "region" | "packaging" | "defect" | "label";
  bounding_box?: [number, number, number, number] | null;
  recognized_text?: { text: string; confidence: number }[];
  data_completion?: {
    status: "complete" | "incomplete" | "review";
    catalog_match: "matched" | "ambiguous" | "none" | "unavailable";
    fields: {
      field: string;
      value: string;
      confidence: number;
      source: "ocr" | "catalog";
      requires_review: boolean;
    }[];
    missing_fields: string[];
    conflicts: string[];
  } | null;
};

export type CheckResult = {
  id: string;
  name: string;
  passed: boolean;
  explanation: string;
  confidence: number;
};

export type InspectionResult = {
  product_name: string;
  category: string;
  inspection_mode: "mock" | "yolo";
  passed: boolean;
  overall_confidence: number;
  summary: string;
  detections: Detection[];
  checks: CheckResult[];
  generated_at: string;
};
