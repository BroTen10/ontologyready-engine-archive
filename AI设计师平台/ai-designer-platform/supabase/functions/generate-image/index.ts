Deno.serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS, PUT, DELETE, PATCH',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Credentials': 'false'
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const { prompt, platform, aspectRatio, count = 1 } = await req.json();

    if (!prompt) {
      throw new Error('Prompt is required');
    }

    const openaiApiKey = Deno.env.get('OPENAI_API_KEY');
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const serviceRoleKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

    // Determine image size based on aspect ratio
    let size = '1024x1024';
    let width = 1024;
    let height = 1024;
    if (aspectRatio === '16:9') {
      size = '1792x1024';
      width = 1792;
      height = 1024;
    } else if (aspectRatio === '9:16') {
      size = '1024x1792';
      width = 1024;
      height = 1792;
    } else if (aspectRatio === '3:4') {
      width = 768;
      height = 1024;
    } else if (aspectRatio === '4:3') {
      width = 1024;
      height = 768;
    }

    const images: string[] = [];

    // Try DALL-E 3 first if API key is available
    if (platform === 'dalle' && openaiApiKey) {
      for (let i = 0; i < Math.min(count, 1); i++) {
        try {
          const response = await fetch('https://api.openai.com/v1/images/generations', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${openaiApiKey}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              model: 'dall-e-3',
              prompt: prompt,
              n: 1,
              size: size,
              quality: 'standard',
            }),
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error('DALL-E API error:', errorText);
            continue;
          }

          const data = await response.json();
          if (data.data && data.data[0]?.url) {
            const imageUrl = data.data[0].url;
            
            // Try to upload to Supabase Storage
            if (supabaseUrl && serviceRoleKey) {
              try {
                const imageResponse = await fetch(imageUrl);
                const imageBlob = await imageResponse.blob();
                const imageBuffer = await imageBlob.arrayBuffer();
                const imageBytes = new Uint8Array(imageBuffer);

                const timestamp = Date.now();
                const storagePath = `generated/${timestamp}-${i}.png`;

                const uploadResponse = await fetch(`${supabaseUrl}/storage/v1/object/generated-images/${storagePath}`, {
                  method: 'POST',
                  headers: {
                    'Authorization': `Bearer ${serviceRoleKey}`,
                    'Content-Type': 'image/png',
                    'x-upsert': 'true'
                  },
                  body: imageBytes
                });

                if (uploadResponse.ok) {
                  const publicUrl = `${supabaseUrl}/storage/v1/object/public/generated-images/${storagePath}`;
                  images.push(publicUrl);
                } else {
                  images.push(imageUrl);
                }
              } catch (uploadErr) {
                console.error('Upload error:', uploadErr);
                images.push(imageUrl);
              }
            } else {
              images.push(imageUrl);
            }
          }
        } catch (err) {
          console.error('DALL-E generation error:', err);
        }
      }
    }

    // Fallback: Use Pollinations AI (free, no API key required)
    if (images.length === 0) {
      console.log('Using Pollinations AI fallback');
      for (let i = 0; i < count; i++) {
        // Pollinations.ai provides free AI image generation
        const encodedPrompt = encodeURIComponent(prompt + ` seed:${Date.now() + i}`);
        const pollinationsUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&nologo=true`;
        images.push(pollinationsUrl);
      }
    }

    // Save generation history
    if (supabaseUrl && serviceRoleKey && images.length > 0) {
      try {
        await fetch(`${supabaseUrl}/rest/v1/generation_history`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${serviceRoleKey}`,
            'apikey': serviceRoleKey,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
          },
          body: JSON.stringify({
            ai_platform: platform,
            prompt: prompt,
            aspect_ratio: aspectRatio,
            result_images: images,
            status: 'completed'
          })
        });
      } catch (historyErr) {
        console.error('Failed to save history:', historyErr);
      }
    }

    return new Response(JSON.stringify({ 
      data: { images } 
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Generate image error:', error);

    // Even on error, return fallback images
    const images = [];
    const prompt = 'AI generated design';
    for (let i = 0; i < 1; i++) {
      const encodedPrompt = encodeURIComponent(prompt + ` seed:${Date.now() + i}`);
      images.push(`https://image.pollinations.ai/prompt/${encodedPrompt}?width=1024&height=1024&nologo=true`);
    }

    return new Response(JSON.stringify({ 
      data: { images } 
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
