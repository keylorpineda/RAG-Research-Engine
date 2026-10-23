import { parseAnswer, parseInline } from './answer-format';

describe('answer format', () => {
  it('splits text, code, bold and citations', () => {
    expect(parseInline('Use `async def` to **declare** them [1].')).toEqual([
      { kind: 'text', value: 'Use ' },
      { kind: 'code', value: 'async def' },
      { kind: 'text', value: ' to ' },
      { kind: 'strong', value: 'declare' },
      { kind: 'text', value: ' them ' },
      { kind: 'cite', n: 1 },
      { kind: 'text', value: '.' },
    ]);
  });

  it('reads italics but leaves lone asterisks and underscores alone', () => {
    expect(parseInline('a *native coroutine* here')).toEqual([
      { kind: 'text', value: 'a ' },
      { kind: 'em', value: 'native coroutine' },
      { kind: 'text', value: ' here' },
    ]);
    expect(parseInline('2 * 3 and __post_init__')).toEqual([
      { kind: 'text', value: '2 * 3 and __post_init__' },
    ]);
  });

  it('reads grouped and adjacent citations', () => {
    const cites = (text: string) =>
      parseInline(text)
        .filter((p) => p.kind === 'cite')
        .map((p) => (p.kind === 'cite' ? p.n : 0));
    expect(cites('A [1, 3] and B [2][4].')).toEqual([1, 3, 2, 4]);
  });

  it('leaves brackets that are not citations as text', () => {
    expect(parseInline('a list like [x, y]')).toEqual([
      { kind: 'text', value: 'a list like [x, y]' },
    ]);
  });

  it('groups paragraphs and bullet or numbered lists', () => {
    const blocks = parseAnswer(
      'First line\ncontinues [1].\n\nSteps:\n1. one [2]\n2. two\n- a\n- b',
    );
    expect(blocks.map((b) => b.kind)).toEqual(['p', 'p', 'ol', 'ul']);
    expect(blocks[0]).toEqual({
      kind: 'p',
      inlines: [
        { kind: 'text', value: 'First line continues ' },
        { kind: 'cite', n: 1 },
        { kind: 'text', value: '.' },
      ],
    });
    const ol = blocks[2];
    expect(ol.kind === 'ol' && ol.items.length).toBe(2);
  });
});
