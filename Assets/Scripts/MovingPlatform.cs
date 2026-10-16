using UnityEngine;

/// <summary>
/// Moves a platform horizontally until it touches the RWall or LWall triggers, then turns around.
/// </summary>
[RequireComponent(typeof(Rigidbody2D))]
public class MovingPlatform : MonoBehaviour
{
    [SerializeField, Min(0f)] float speed = 2f;

    Rigidbody2D body;
    float direction = 1f;

    public Vector2 Velocity => new Vector2(direction * speed, 0f);

    void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        body.bodyType = RigidbodyType2D.Kinematic;
        body.gravityScale = 0f;
        body.freezeRotation = true;
        body.interpolation = RigidbodyInterpolation2D.Interpolate;
        body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
    }

    void FixedUpdate()
    {
        body.MovePosition(body.position + Velocity * Time.fixedDeltaTime);
    }

    void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("RWall"))
            direction = -1f;
        else if (other.CompareTag("LWall"))
            direction = 1f;
    }
}
