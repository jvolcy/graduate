using UnityEngine;
using UnityEngine.InputSystem;

/// <summary>
/// Side-view movement for the player. Drives the Animator with Speed, Grounded, and Die.
/// </summary>
[RequireComponent(typeof(Rigidbody2D))]
[RequireComponent(typeof(SpriteRenderer))]
[RequireComponent(typeof(Animator))]
public class PlayerController : MonoBehaviour
{
    [SerializeField] float moveSpeed = 5f;
    [SerializeField] float jumpSpeed = 11f;
    [SerializeField] float gravityScale = 3f;
    [SerializeField] float fallDeathY = -8f;
    [SerializeField] bool followWithCamera = true;

    Rigidbody2D body;
    SpriteRenderer spriteRenderer;
    Animator animator;
    float moveAxis;
    float jumpLock;
    float carryX;
    bool dead;
    readonly ContactPoint2D[] groundContacts = new ContactPoint2D[8];

    static readonly int SpeedId = Animator.StringToHash("Speed");
    static readonly int GroundedId = Animator.StringToHash("Grounded");
    static readonly int DieId = Animator.StringToHash("Die");

    public bool IsDead => dead;

    void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        spriteRenderer = GetComponent<SpriteRenderer>();
        animator = GetComponent<Animator>();
        body.freezeRotation = true;
        body.gravityScale = gravityScale;
        body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        body.interpolation = RigidbodyInterpolation2D.Interpolate;
    }

    void Update()
    {
        if (!dead && transform.position.y < fallDeathY)
            Die();

        if (dead)
        {
            animator.SetBool(GroundedId, false);
            return;
        }

        moveAxis = ReadMove();
        MovingPlatform platform;
        bool grounded = CheckGround(out platform);
        if (grounded && jumpLock <= 0f)
            carryX = platform != null ? platform.Velocity.x : 0f;
        else if (jumpLock <= 0f)
            carryX = 0f;

        if (ReadJumpPressed() && grounded && jumpLock <= 0f)
        {
            body.linearVelocity = new Vector2(body.linearVelocity.x, jumpSpeed);
            grounded = false;
            jumpLock = 0.12f;
        }

        if (jumpLock > 0f)
        {
            jumpLock -= Time.deltaTime;
            grounded = false;
        }

        if (moveAxis > 0.01f)
            spriteRenderer.flipX = false;
        else if (moveAxis < -0.01f)
            spriteRenderer.flipX = true;

        animator.SetFloat(SpeedId, Mathf.Abs(moveAxis));
        animator.SetBool(GroundedId, grounded);
    }

    void FixedUpdate()
    {
        if (dead)
        {
            body.linearVelocity = new Vector2(0f, body.linearVelocity.y);
            return;
        }

        if (jumpLock <= 0f)
        {
            MovingPlatform platform;
            if (CheckGround(out platform))
            {
                carryX = platform != null ? platform.Velocity.x : 0f;
                if (body.linearVelocity.y > 0f)
                    body.linearVelocity = new Vector2(body.linearVelocity.x, 0f);
            }
            else
                carryX = 0f;
        }

        body.linearVelocity = new Vector2(moveAxis * moveSpeed + carryX, body.linearVelocity.y);
    }

    void LateUpdate()
    {
        if (!followWithCamera)
            return;

        var cam = Camera.main;
        if (cam == null)
            return;

        var position = cam.transform.position;
        cam.transform.position = new Vector3(transform.position.x, transform.position.y, position.z);
    }

    /// <summary>
    /// Plays the die clip and stops control. Safe to call more than once.
    /// </summary>
    public void Die()
    {
        if (dead)
            return;

        dead = true;
        moveAxis = 0f;
        carryX = 0f;
        animator.SetTrigger(DieId);
        body.linearVelocity = new Vector2(0f, body.linearVelocity.y);
    }

    float ReadMove()
    {
        float move = 0f;
        var keyboard = Keyboard.current;
        if (keyboard != null)
        {
            if (keyboard.aKey.isPressed || keyboard.leftArrowKey.isPressed)
                move -= 1f;
            if (keyboard.dKey.isPressed || keyboard.rightArrowKey.isPressed)
                move += 1f;
        }

        var pad = Gamepad.current;
        if (pad != null)
        {
            float stick = pad.leftStick.x.ReadValue();
            if (Mathf.Abs(stick) > 0.2f)
                move = stick;
            if (pad.dpad.left.isPressed)
                move = -1f;
            if (pad.dpad.right.isPressed)
                move = 1f;
        }

        return Mathf.Clamp(move, -1f, 1f);
    }

    bool ReadJumpPressed()
    {
        var keyboard = Keyboard.current;
        if (keyboard != null &&
            (keyboard.spaceKey.wasPressedThisFrame ||
             keyboard.wKey.wasPressedThisFrame ||
             keyboard.upArrowKey.wasPressedThisFrame))
            return true;

        var pad = Gamepad.current;
        return pad != null &&
               (pad.buttonSouth.wasPressedThisFrame || pad.dpad.up.wasPressedThisFrame);
    }

    bool CheckGround(out MovingPlatform platform)
    {
        platform = null;
        int contactCount = body.GetContacts(groundContacts);
        for (int i = 0; i < contactCount; i++)
        {
            var contact = groundContacts[i];

            // Only a surface pushing upward is ground. Side contacts must not
            // activate platform carrying or the player will cling to walls.
            if (contact.normal.y < 0.5f)
                continue;

            var other = contact.collider.attachedRigidbody == body
                ? contact.otherCollider
                : contact.collider;
            platform = other.GetComponentInParent<MovingPlatform>();
            return true;
        }

        return false;
    }
}
