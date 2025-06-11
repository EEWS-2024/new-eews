import {CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis} from "recharts";

export default function Chart({data, phasePicking}: {
    data: { time: number, value: number }[];
    phasePicking: {pArrivalTime: number | null, sArrivalTime: number | null};
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
                    <Tooltip content={({ active, payload, label }) => {
                        if (!active || !payload || !payload.length) return null;

                        return (
                            <div className="bg-gray-900 p-2 rounded shadow text-sm">
                                <p>Time: {new Date(label).toLocaleTimeString()}</p>
                                {payload.map((entry, index) => (
                                    <p key={index}>
                                        <p>Value: {entry.value && Number(entry.value).toFixed(2)}</p>
                                    </p>
                                ))}
                            </div>
                        );
                    }}/>
                    <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} dot={false} />
                    {
                        phasePicking.sArrivalTime &&
                        <ReferenceLine stroke="red" strokeWidth={2} x={phasePicking.sArrivalTime} />
                    }
                    {
                        phasePicking.pArrivalTime &&
                        <ReferenceLine stroke="yellow" strokeWidth={2} x={phasePicking.pArrivalTime} />
                    }

                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}