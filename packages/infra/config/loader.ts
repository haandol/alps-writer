import * as fs from "fs";
import * as path from "path";
import * as joi from "joi";
import * as toml from "toml";

interface IConfig {
  app: {
    ns: string;
    stage: "Dev" | "Prod";
  };
  vpc?: {
    vpcId?: string;
  };
  auth: {
    callbackUrls: string[];
  };
  chatbot: {
    bedrockModelId: string;
    tableName: string;
  };
  external: {
    web: {
      tavilyApiKey: string;
    };
  };
}

const cfg = toml.parse(
  fs.readFileSync(path.resolve(__dirname, "..", ".toml"), "utf-8")
);
console.log("loaded config", JSON.stringify(cfg, null, 2));

const schema = joi
  .object({
    app: joi
      .object({
        ns: joi.string().required(),
        stage: joi.string().valid("Dev", "Prod").required(),
      })
      .required(),
    vpc: joi
      .object({
        vpcId: joi.string().optional(),
      })
      .optional(),
    auth: joi.object({
      callbackUrls: joi.array().items(joi.string()).required(),
    }),
    chatbot: joi
      .object({
        bedrockModelId: joi.string().required(),
        tableName: joi.string().required(),
      })
      .required(),
    external: joi
      .object({
        web: joi
          .object({
            tavilyApiKey: joi.string().required(),
          })
          .required(),
      })
      .required(),
  })
  .unknown();

const { error } = schema.validate(cfg);

if (error) {
  throw new Error(`Config validation error: ${error.message}`);
}

export const Config: IConfig = {
  ...cfg,
  app: {
    ...cfg.app,
    ns: `${cfg.app.ns}${cfg.app.stage}`,
  },
};
