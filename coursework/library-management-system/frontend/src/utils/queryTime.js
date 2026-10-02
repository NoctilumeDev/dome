// 日期选择器提供本地日历日期；不要转换成 UTC 后再截取日期。
export function toQueryRange(dates) {
  if (!Array.isArray(dates) || dates.length !== 2) return { startTime: null, endTime: null };
  const days = dates.map(date => {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) throw new Error('无效日期');
    const pad = value => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  });
  return { startTime: `${days[0]}T00:00:00`, endTime: `${days[1]}T23:59:59` };
}
