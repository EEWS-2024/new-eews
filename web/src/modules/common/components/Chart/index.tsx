import {CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";

export default function Chart({data}: {
    data: { time: number, value: number }[];
}) {
    return (
        <div className="w-full h-[150px]">
            <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="time"
                        xAxisId={0}
                        axisLine={true}
                        ticks={data.filter((_, i) => i % Math.floor(data.length / 5) === 0).map(d => d.time)}
                        domain={['auto', 'auto']}
                        padding={'gap'}
                        tickFormatter={(val) => new Date(val).toLocaleTimeString('en-US', {
                            hourCycle: 'h24',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit',
                        })

                        }/>
                    <YAxis
                        type="number"
                        domain={([dataMin, dataMax]) => {
                            const absMax = Math.max(
                                Math.abs(dataMin),
                                Math.abs(dataMax),
                                5000
                            );
                            return [-absMax, absMax];
                        }}
                        ticks={[0]}
                    />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} dot={false} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}