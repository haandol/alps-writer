import * as fs from "fs";
import * as path from "path";
import { z } from "zod";
import * as toml from "toml";

const ConfigSchema = z.object({
  app: z
    .object({
      ns: z.string(),
      stage: z.enum(["Dev", "Prod"]),
    })
    .required(),
  vpc: z
    .object({
      vpcId: z.string(),
    })
    .optional(),
  auth: z
    .object({
      callbackUrls: z.array(z.string()),
    })
    .required(),
  chatbot: z
    .object({
      bedrockModelId: z.string(),
      tableName: z.string(),
    })
    .required(),
  external: z
    .object({
      web: z
        .object({
          tavilyApiKey: z.string(),
        })
        .required(),
    })
    .required(),
});

type IConfig = z.infer<typeof ConfigSchema>;

const cfg = toml.parse(
  fs.readFileSync(path.resolve(__dirname, "..", ".toml"), "utf-8")
);
console.log("loaded config", JSON.stringify(cfg, null, 2));

// zod validation
const result = ConfigSchema.safeParse(cfg);

if (!result.success) {
  throw new Error(`Config validation error: ${result.error.message}`);
}

export const Config: IConfig = {
  ...result.data,
  app: {
    ...result.data.app,
    ns: `${result.data.app.ns}${result.data.app.stage}`,
  },
};
