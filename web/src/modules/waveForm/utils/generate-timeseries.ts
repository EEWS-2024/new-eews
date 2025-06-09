import {WaveForm} from "@/modules/waveForm/stores/interface";

export const generateTimeSeries = (waveForm: WaveForm[], sampleRate: number) => {
    const waveforms: any[] = [];
    const missingPacket = 50 - waveForm.length;

    if (missingPacket > 0 && waveForm[0]) {
        const before = new Date(waveForm[0].start_time).getTime()
        const tick = 1000 / sampleRate;
        const totalLostData = 128 * missingPacket
        const waveformsWithTime = Array(totalLostData).fill(null).map((_, idx)=>{
            return {
                value: 0,
                time: before - (totalLostData - idx) * tick
            }
        });
        waveforms.push(...waveformsWithTime);
    }


    waveForm.forEach((packet) => {
        const current = new Date(packet.start_time).getTime();
        const endtime = new Date(packet.end_time).getTime();
        const tick = Math.round(endtime - current) / packet.data.length;
        const waveformsWithTime = packet.data.map((value, idx) => {
            return {
                value,
                time: current + idx * tick
            };
        });
        waveforms.push(...waveformsWithTime);
    });

    return waveforms;
}