// Copied from docs/assessment-api/examples.json; fictional UI fixtures only.
export default {
  "queued": {
    "task_id": "mock-task-quick",
    "type": "quick_analysis",
    "session_id": "mock-session",
    "status": "queued",
    "current_stage": null,
    "agent_tasks": [],
    "result": null,
    "error": null,
    "created_at": "2026-11-02T04:00:00Z",
    "updated_at": "2026-11-02T04:00:00Z"
  },
  "completed": {
    "task_id": "mock-task-quick",
    "type": "quick_analysis",
    "session_id": "mock-session",
    "status": "completed",
    "current_stage": "mock-stage",
    "agent_tasks": [],
    "result": {
      "kind": "analysis",
      "analysis": {
        "id": "mock-analysis-quick",
        "mode": "quick",
        "measurement_ids": [
          "mock-measurement-1"
        ],
        "input_snapshot": [
          {
            "source_type": "measurement",
            "source_id": "mock-measurement-1",
            "indicator_code": "soil_ph",
            "label": "Mock 单项录入；不是实际地块实测资料"
          }
        ],
        "coverage": {
          "recommended_codes": [],
          "measured_codes": [
            "soil_ph"
          ],
          "missing_codes": [],
          "extra_codes": [
            "soil_ph"
          ]
        },
        "assessment": {
          "summary": "界面示例：收到一项指标，可以展示对应范围的说明。",
          "scope": "single_indicator",
          "composite_score": null,
          "score_explanation": "未计算综合分数；此内容为接口演示，不是科学评价。",
          "indicator_assessments": [
            {
              "indicator_code": "soil_ph",
              "status": "descriptive_only",
              "explanation": "原值为6.2；本示例不配置评价阈值。",
              "evidence": [
                {
                  "source_type": "measurement",
                  "source_id": "mock-measurement-1",
                  "indicator_code": "soil_ph",
                  "label": "Mock 单项录入；不是实际地块实测资料"
                }
              ]
            }
          ]
        },
        "problems": [
          {
            "id": "mock-problem",
            "title": "检测背景仍需核对",
            "observation": "当前仅提供一项指标，缺少检测方法和地块背景。",
            "possible_causes": [],
            "priority": "undetermined",
            "evidence": [
              {
                "source_type": "measurement",
                "source_id": "mock-measurement-1",
                "indicator_code": "soil_ph",
                "label": "Mock 单项录入；不是实际地块实测资料"
              }
            ],
            "verification_needed": [
              "核对检测方法与采样条件"
            ]
          }
        ],
        "decisions": [
          {
            "id": "mock-decision",
            "action": "先核对检测记录和管理背景",
            "reason": "示例只支持有限范围的说明。",
            "conditions": [
              "此建议仅用于前端展示结构"
            ],
            "timing": null,
            "verification_goal": "使下一次判读有明确输入依据",
            "evidence": [
              {
                "source_type": "measurement",
                "source_id": "mock-measurement-1",
                "indicator_code": "soil_ph",
                "label": "Mock 单项录入；不是实际地块实测资料"
              }
            ]
          }
        ],
        "gaps": [
          "方法、土层和作物信息未确认"
        ],
        "optional_tests": [],
        "next_plan_id": null,
        "model_info": {
          "model_name": "mock-placeholder-not-a-deployed-model",
          "model_version": null,
          "is_fine_tuned": false,
          "rule_version": null
        },
        "limitations": [
          "所有内容均为Mock，不代表实际模型能力或正式健康结论。"
        ],
        "created_at": "2026-11-02T04:00:00Z"
      }
    },
    "error": null,
    "created_at": "2026-11-02T04:00:00Z",
    "updated_at": "2026-11-02T04:00:00Z"
  },
  "partial": {
    "task_id": "mock-task-partial",
    "type": "quick_analysis",
    "session_id": "mock-session",
    "status": "partial",
    "current_stage": "mock-stage",
    "agent_tasks": [],
    "result": {
      "kind": "analysis",
      "analysis": {
        "id": "mock-analysis-quick",
        "mode": "quick",
        "measurement_ids": [
          "mock-measurement-1"
        ],
        "input_snapshot": [
          {
            "source_type": "measurement",
            "source_id": "mock-measurement-1",
            "indicator_code": "soil_ph",
            "label": "Mock 单项录入；不是实际地块实测资料"
          }
        ],
        "coverage": {
          "recommended_codes": [],
          "measured_codes": [
            "soil_ph"
          ],
          "missing_codes": [],
          "extra_codes": [
            "soil_ph"
          ]
        },
        "assessment": {
          "summary": "界面示例：收到一项指标，可以展示对应范围的说明。",
          "scope": "single_indicator",
          "composite_score": null,
          "score_explanation": "未计算综合分数；此内容为接口演示，不是科学评价。",
          "indicator_assessments": [
            {
              "indicator_code": "soil_ph",
              "status": "descriptive_only",
              "explanation": "原值为6.2；本示例不配置评价阈值。",
              "evidence": [
                {
                  "source_type": "measurement",
                  "source_id": "mock-measurement-1",
                  "indicator_code": "soil_ph",
                  "label": "Mock 单项录入；不是实际地块实测资料"
                }
              ]
            }
          ]
        },
        "problems": [
          {
            "id": "mock-problem",
            "title": "检测背景仍需核对",
            "observation": "当前仅提供一项指标，缺少检测方法和地块背景。",
            "possible_causes": [],
            "priority": "undetermined",
            "evidence": [
              {
                "source_type": "measurement",
                "source_id": "mock-measurement-1",
                "indicator_code": "soil_ph",
                "label": "Mock 单项录入；不是实际地块实测资料"
              }
            ],
            "verification_needed": [
              "核对检测方法与采样条件"
            ]
          }
        ],
        "decisions": [
          {
            "id": "mock-decision",
            "action": "先核对检测记录和管理背景",
            "reason": "示例只支持有限范围的说明。",
            "conditions": [
              "此建议仅用于前端展示结构"
            ],
            "timing": null,
            "verification_goal": "使下一次判读有明确输入依据",
            "evidence": [
              {
                "source_type": "measurement",
                "source_id": "mock-measurement-1",
                "indicator_code": "soil_ph",
                "label": "Mock 单项录入；不是实际地块实测资料"
              }
            ]
          }
        ],
        "gaps": [
          "方法、土层和作物信息未确认"
        ],
        "optional_tests": [],
        "next_plan_id": null,
        "model_info": {
          "model_name": "mock-placeholder-not-a-deployed-model",
          "model_version": null,
          "is_fine_tuned": false,
          "rule_version": null
        },
        "limitations": [
          "所有内容均为Mock，不代表实际模型能力或正式健康结论。"
        ],
        "created_at": "2026-11-02T04:00:00Z"
      }
    },
    "error": null,
    "created_at": "2026-11-02T04:00:00Z",
    "updated_at": "2026-11-02T04:00:00Z"
  },
  "failed": {
    "task_id": "mock-task-failed",
    "type": "quick_analysis",
    "session_id": "mock-session",
    "status": "failed",
    "current_stage": "mock-stage",
    "agent_tasks": [],
    "result": null,
    "error": {
      "code": "TASK_FAILED",
      "message": "接口开发演示状态，不是真实服务或模型故障。",
      "fields": [],
      "retryable": true
    },
    "created_at": "2026-11-02T04:00:00Z",
    "updated_at": "2026-11-02T04:00:00Z"
  },
  "interrupted": {
    "task_id": "mock-task-interrupted",
    "type": "quick_analysis",
    "session_id": "mock-session",
    "status": "interrupted",
    "current_stage": "mock-stage",
    "agent_tasks": [],
    "result": null,
    "error": {
      "code": "TASK_INTERRUPTED",
      "message": "接口开发演示状态，不是真实服务或模型故障。",
      "fields": [],
      "retryable": true
    },
    "created_at": "2026-11-02T04:00:00Z",
    "updated_at": "2026-11-02T04:00:00Z"
  },
  "running": {
    "task_id": "mock-task-quick",
    "type": "quick_analysis",
    "session_id": "mock-session",
    "status": "running",
    "current_stage": "mock-stage",
    "agent_tasks": [],
    "result": null,
    "error": null,
    "created_at": "2026-11-02T04:00:00Z",
    "updated_at": "2026-11-02T04:00:00Z"
  }
}
