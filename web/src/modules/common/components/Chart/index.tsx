import {CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";

export default function Chart({data, interval}: {
    data?: any[];
    interval?: number;
}) {
    return (
        <div className="w-full h-[300px]">
            <ResponsiveContainer width="100%" height="50%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="time"
                        xAxisId={0}
                        axisLine={true}
                        tickSize={10}
                        interval={interval}
                        domain={['auto', 'auto']}
                        padding={'gap'}
                        tickFormatter={(val) => {
                            console.log('Tick:', val, new Date(val).toLocaleTimeString());
                            return new Date(val).toLocaleTimeString('en-US', {
                                    hourCycle: 'h24',
                                    hour: '2-digit',
                                    minute: '2-digit',
                                    second: '2-digit',
                                })
                        }

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