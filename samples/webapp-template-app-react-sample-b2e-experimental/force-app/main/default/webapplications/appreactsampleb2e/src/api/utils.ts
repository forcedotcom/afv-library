// Simple gql template tag function
export const gql = (strings: TemplateStringsArray, ...values: unknown[]): string => {
	return strings.reduce((result, str, i) => result + str + (values[i] ?? ""), "");
};
